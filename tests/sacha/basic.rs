#[kani::proof]
pub fn main() {
    let x: i32 = kani::any();
    kani::assume(x >= 0);
    assert!(x < 100);
}
