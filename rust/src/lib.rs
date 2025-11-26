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
#[derive(Debug)]
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
            .bind(py)
            .name()
            .map(|n| n.to_string())
            .unwrap_or_else(|_| "<unknown>".to_string())
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

impl Clone for TypeKey {
    fn clone(&self) -> Self {
        Python::attach(|py| TypeKey {
            py_type: self.py_type.clone_ref(py),
        })
    }
}

/// Provider variants for different creation strategies
pub enum Provider {
    /// Pre-created instance
    Instance(Py<PyAny>),

    /// Class to instantiate (calls __init__)
    Class(Py<PyType>),

    /// Factory function to invoke (singleton - caches result)
    SingletonFactory(Py<PyAny>),

    /// Factory function to invoke (transient - creates new each time)
    TransientFactory(Py<PyAny>),
}

impl Clone for Provider {
    fn clone(&self) -> Self {
        Python::attach(|py| match self {
            Provider::Instance(obj) => Provider::Instance(obj.clone_ref(py)),
            Provider::Class(cls) => Provider::Class(cls.clone_ref(py)),
            Provider::SingletonFactory(factory) => {
                Provider::SingletonFactory(factory.clone_ref(py))
            }
            Provider::TransientFactory(factory) => {
                Provider::TransientFactory(factory.clone_ref(py))
            }
        })
    }
}

/// Core Rust container implementation
pub struct RustContainer {
    /// Provider registry: maps Python type to Provider
    providers: Arc<RwLock<HashMap<TypeKey, Provider>>>,

    /// Singleton instance cache: maps Python type to cached instance
    singletons: Arc<RwLock<HashMap<TypeKey, Py<PyAny>>>>,
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
        instance: Py<PyAny>,
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

    /// Register a singleton factory provider (caches result)
    pub fn register_singleton_factory(
        &self,
        py: Python,
        type_key: TypeKey,
        factory: Py<PyAny>,
    ) -> Result<(), ContainerError> {
        let mut providers = self.providers.write().unwrap();

        // Check for duplicate registration
        if providers.contains_key(&type_key) {
            return Err(ContainerError::DuplicateRegistration {
                type_name: type_key.type_name(py),
            });
        }

        providers.insert(type_key, Provider::SingletonFactory(factory));
        Ok(())
    }

    /// Register a transient factory provider (creates new instance each time)
    pub fn register_transient_factory(
        &self,
        py: Python,
        type_key: TypeKey,
        factory: Py<PyAny>,
    ) -> Result<(), ContainerError> {
        let mut providers = self.providers.write().unwrap();

        // Check for duplicate registration
        if providers.contains_key(&type_key) {
            return Err(ContainerError::DuplicateRegistration {
                type_name: type_key.type_name(py),
            });
        }

        providers.insert(type_key, Provider::TransientFactory(factory));
        Ok(())
    }

    /// Resolve a dependency by type
    pub fn resolve(&self, py: Python, type_key: &TypeKey) -> Result<Py<PyAny>, ContainerError> {
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
            Provider::Instance(obj) => {
                // Instance providers are always singletons (pre-created)
                obj.clone_ref(py)
            }
            Provider::Class(cls) => {
                // Class providers create new instances each time (transient)
                cls.call0(py)?
            }
            Provider::SingletonFactory(factory) => {
                // Singleton factory - call once and cache result
                let instance = factory.call0(py)?;

                // Cache the factory result
                let mut singletons = self.singletons.write().unwrap();
                singletons.insert(type_key.clone(), instance.clone_ref(py));

                instance
            }
            Provider::TransientFactory(factory) => {
                // Transient factory - create new instance each time (no caching)
                factory.call0(py)?
            }
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

    /// Clear the singleton instance cache (keep provider registrations)
    pub fn reset(&self) {
        self.singletons.write().unwrap().clear();
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
    fn register_instance(
        &self,
        py: Python,
        py_type: &Bound<'_, PyType>,
        instance: Py<PyAny>,
    ) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.clone().unbind());
        self.rust_core
            .register_instance(py, type_key, instance)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Register a class for a given type
    fn register_class(
        &self,
        py: Python,
        py_type: &Bound<'_, PyType>,
        class: &Bound<'_, PyType>,
    ) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.clone().unbind());
        self.rust_core
            .register_class(py, type_key, class.clone().unbind())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Register a singleton factory function for a given type (caches result)
    fn register_singleton_factory(
        &self,
        py: Python,
        py_type: &Bound<'_, PyType>,
        factory: Py<PyAny>,
    ) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.clone().unbind());
        self.rust_core
            .register_singleton_factory(py, type_key, factory)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Register a transient factory function for a given type (creates new instance each time)
    fn register_transient_factory(
        &self,
        py: Python,
        py_type: &Bound<'_, PyType>,
        factory: Py<PyAny>,
    ) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.clone().unbind());
        self.rust_core
            .register_transient_factory(py, type_key, factory)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyKeyError, _>(e.to_string()))
    }

    /// Resolve a dependency by type
    fn resolve(&self, py: Python, py_type: &Bound<'_, PyType>) -> PyResult<Py<PyAny>> {
        let type_key = TypeKey::new(py_type.clone().unbind());
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

    /// Clear cached singleton instances for test isolation
    fn reset(&self) {
        self.rust_core.reset();
    }
}

/// Rust-backed dependency injection core
#[pymodule]
fn _dioxide_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Container>()?;
    Ok(())
}
