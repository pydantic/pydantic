use std::process::Command;
use std::str::from_utf8;

fn generate_self_schema() {
    let output = Command::new("python")
        .arg("generate_self_schema.py")
        .output()
        .expect("failed to execute process");

    if !output.status.success() {
        let stdout = from_utf8(&output.stdout).unwrap();
        let stderr = from_utf8(&output.stderr).unwrap();
        eprint!("{}{}", stdout, stderr);
        panic!("generate_self_schema.py failed with {}", output.status);
    }
}

fn main() {
    pyo3_build_config::use_pyo3_cfgs();
    if let Some(true) = version_check::supports_feature("no_coverage") {
        println!("cargo:rustc-cfg=has_no_coverage");
    }
    generate_self_schema()
}
