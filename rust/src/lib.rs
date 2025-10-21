use pyo3::prelude::*;

/// Rust-backed dependency injection core
#[pymodule]
fn _rivet_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Container>()?;
    Ok(())
}

/// Dependency injection container
#[pyclass]
struct Container {
    // Graph and state will be added in walking skeleton
}

#[pymethods]
impl Container {
    #[new]
    fn new() -> Self {
        Container {}
    }

    fn resolve(&self, _py: Python, _type_name: &str) -> PyResult<PyObject> {
        // Will be implemented in walking skeleton
        todo!("resolve not yet implemented")
    }
}
