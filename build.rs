use std::path::Path;
use std::process::Command;
use std::str::from_utf8;

fn generate_self_schema() {
    println!("cargo:rerun-if-changed=pydantic_core/core_schema.py");
    println!("cargo:rerun-if-changed=generate_self_schema.py");
    if Path::new("./src/self_schema.py").exists() && option_env!("DEBIAN_FRONTEND") == Some("noninteractive") {
        // self_schema.py already exists and DEBIAN_FRONTEND indicates we're in a maturin build,
        // skip running generate_self_schema.py
        return;
    }
    let output = Command::new("python3")
        .arg("generate_self_schema.py")
        .output()
        .expect("failed to execute process");

    if !output.status.success() {
        let stdout = from_utf8(&output.stdout).unwrap();
        let stderr = from_utf8(&output.stderr).unwrap();
        eprint!("{stdout}{stderr}");
        panic!("generate_self_schema.py failed with {}", output.status);
    }
}

fn main() {
    pyo3_build_config::use_pyo3_cfgs();
    if let Some(true) = version_check::supports_feature("no_coverage") {
        println!("cargo:rustc-cfg=has_no_coverage");
    }
    generate_self_schema();
    println!("cargo:rustc-env=PROFILE={}", std::env::var("PROFILE").unwrap());
}
