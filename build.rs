use std::env;
use std::path::Path;
use std::process::Command;
use std::str::from_utf8;

fn generate_self_schema() {
    println!("cargo:rerun-if-changed=python/pydantic_core/core_schema.py");
    println!("cargo:rerun-if-changed=generate_self_schema.py");
    if Path::new("./src/self_schema.py").exists() && option_env!("CI") == Some("true") {
        // self_schema.py already exists and CI indicates we're running on a github actions build,
        // don't bother generating again
        return;
    }

    let output = Command::new(
        env::var("PYTHON")
            .ok()
            .or_else(|| pyo3_build_config::get().executable.clone())
            .unwrap_or_else(|| "python3".to_owned()),
    )
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
