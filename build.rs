fn main() {
    pyo3_build_config::use_pyo3_cfgs();
    if let Some(true) = version_check::supports_feature("no_coverage") {
        println!("cargo:rustc-cfg=has_no_coverage");
    }
}
