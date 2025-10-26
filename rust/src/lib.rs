use pyo3::prelude::*;
use pyo3::types::PyType;
use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::sync::{Arc, RwLock};
use thiserror::Error;

/// Container error types
#[derive(Error, Debug)]
pub enum ContainerError {
    #[error("Dependency not registered: {type_name}")]
    DependencyNotRegistered { type_name: String },

    #[error("Provider registration failed: {type_name} - {reason}")]
    ProviderRegistrationFailed { type_name: String, reason: String },

    #[error("Duplicate provider registration: {type_name}")]
    DuplicateRegistration { type_name: String },

    #[error("Python error: {0}")]
    PythonError(String),
}

impl From<PyErr> for ContainerError {
    fn from(err: PyErr) -> Self {
        ContainerError::PythonError(err.to_string())
    }
}

/// Type key for provider registry (Python type object)
#[derive(Debug, Clone)]
pub struct TypeKey {
    /// Python type object (class)
    py_type: Py<PyType>,
}

impl TypeKey {
    pub fn new(py_type: Py<PyType>) -> Self {
        TypeKey { py_type }
    }

    pub fn type_name(&self, py: Python) -> String {
        self.py_type
            .as_ref(py)
            .name()
            .unwrap_or("<unknown>")
            .to_string()
    }
}

impl Hash for TypeKey {
    fn hash<H: Hasher>(&self, state: &mut H) {
        // Hash the pointer to the Python type object
        // This is safe because type objects are immortal
        self.py_type.as_ptr().hash(state);
    }
}

impl PartialEq for TypeKey {
    fn eq(&self, other: &Self) -> bool {
        // Compare pointer equality (type objects are unique)
        self.py_type.as_ptr() == other.py_type.as_ptr()
    }
}

impl Eq for TypeKey {}

/// Provider variants for different creation strategies
#[derive(Clone)]
pub enum Provider {
    /// Pre-created instance
    Instance(PyObject),

    /// Class to instantiate (calls __init__)
    Class(Py<PyType>),

    /// Factory function to invoke
    Factory(PyObject),
}

/// Core Rust container implementation
pub struct RustContainer {
    /// Provider registry: maps Python type to Provider
    providers: Arc<RwLock<HashMap<TypeKey, Provider>>>,

    /// Singleton instance cache: maps Python type to cached instance
    singletons: Arc<RwLock<HashMap<TypeKey, PyObject>>>,
}

impl RustContainer {
    /// Create a new empty container
    pub fn new() -> Self {
        RustContainer {
            providers: Arc::new(RwLock::new(HashMap::new())),
            singletons: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Register an instance provider
    pub fn register_instance(
        &self,
        py: Python,
        type_key: TypeKey,
        instance: PyObject,
    ) -> Result<(), ContainerError> {
        let mut providers = self.providers.write().unwrap();

        // Check for duplicate registration
        if providers.contains_key(&type_key) {
            return Err(ContainerError::DuplicateRegistration {
                type_name: type_key.type_name(py),
            });
        }

        providers.insert(type_key, Provider::Instance(instance));
        Ok(())
    }

    /// Register a class provider
    pub fn register_class(
        &self,
        py: Python,
        type_key: TypeKey,
        class: Py<PyType>,
    ) -> Result<(), ContainerError> {
        let mut providers = self.providers.write().unwrap();

        // Check for duplicate registration
        if providers.contains_key(&type_key) {
            return Err(ContainerError::DuplicateRegistration {
                type_name: type_key.type_name(py),
            });
        }

        providers.insert(type_key, Provider::Class(class));
        Ok(())
    }

    /// Register a factory provider
    pub fn register_factory(
        &self,
        py: Python,
        type_key: TypeKey,
        factory: PyObject,
    ) -> Result<(), ContainerError> {
        let mut providers = self.providers.write().unwrap();

        // Check for duplicate registration
        if providers.contains_key(&type_key) {
            return Err(ContainerError::DuplicateRegistration {
                type_name: type_key.type_name(py),
            });
        }

        providers.insert(type_key, Provider::Factory(factory));
        Ok(())
    }

    /// Resolve a dependency by type
    pub fn resolve(&self, py: Python, type_key: &TypeKey) -> Result<PyObject, ContainerError> {
        // Check singleton cache first
        {
            let singletons = self.singletons.read().unwrap();
            if let Some(instance) = singletons.get(type_key) {
                return Ok(instance.clone_ref(py));
            }
        }

        // Get provider
        let provider = {
            let providers = self.providers.read().unwrap();
            providers.get(type_key).cloned().ok_or_else(|| {
                ContainerError::DependencyNotRegistered {
                    type_name: type_key.type_name(py),
                }
            })?
        };

        // Create instance based on provider type
        let instance = match provider {
            Provider::Instance(obj) => obj.clone_ref(py),
            Provider::Class(cls) => cls.call0(py)?,
            Provider::Factory(factory) => factory.call0(py)?,
        };

        Ok(instance)
    }

    /// Check if container is empty
    pub fn is_empty(&self) -> bool {
        self.providers.read().unwrap().is_empty()
    }

    /// Get count of registered providers
    pub fn len(&self) -> usize {
        self.providers.read().unwrap().len()
    }
}

impl Default for RustContainer {
    fn default() -> Self {
        Self::new()
    }
}

/// Python-exposed Container class
#[pyclass(name = "Container")]
struct Container {
    rust_core: RustContainer,
}

#[allow(non_local_definitions)]
#[pymethods]
impl Container {
    #[new]
    fn new() -> Self {
        Container {
            rust_core: RustContainer::new(),
        }
    }

    /// Register an instance for a given type
    fn register_instance(&self, py: Python, py_type: &PyType, instance: PyObject) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.into());
        self.rust_core
            .register_instance(py, type_key, instance)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Register a class for a given type
    fn register_class(&self, py: Python, py_type: &PyType, class: &PyType) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.into());
        self.rust_core
            .register_class(py, type_key, class.into())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Register a factory function for a given type
    fn register_factory(&self, py: Python, py_type: &PyType, factory: PyObject) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.into());
        self.rust_core
            .register_factory(py, type_key, factory)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Resolve a dependency by type
    fn resolve(&self, py: Python, py_type: &PyType) -> PyResult<PyObject> {
        let type_key = TypeKey::new(py_type.into());
        self.rust_core
            .resolve(py, &type_key)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Check if container is empty
    fn is_empty(&self) -> bool {
        self.rust_core.is_empty()
    }

    /// Get count of registered providers
    fn __len__(&self) -> usize {
        self.rust_core.len()
    }
}

/// Rust-backed dependency injection core
#[pymodule]
fn _dioxide_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Container>()?;
    Ok(())
}
