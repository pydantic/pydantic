fn main() {
    if let Some(true) = version_check::supports_feature("no_coverage") {
        println!("cargo:rustc-cfg=has_no_coverage");
    }
}
