fn main() {
    pyo3_build_config::use_pyo3_cfgs();
    if let Some(true) = version_check::supports_feature("coverage_attribute") {
        println!("cargo:rustc-cfg=has_coverage_attribute");
    }
    println!("cargo:rustc-check-cfg=cfg(has_coverage_attribute)");

    if std::env::var("RUSTFLAGS")
        .unwrap_or_default()
        .contains("-Cprofile-use=")
    {
        println!("cargo:rustc-cfg=specified_profile_use");
    }
    println!("cargo:rustc-check-cfg=cfg(specified_profile_use)");
    println!("cargo:rustc-env=PROFILE={}", std::env::var("PROFILE").unwrap());
}
