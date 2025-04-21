(module
  (func $double (param $x i32) (result i32)
    local.get $x
    i32.const 2
    i32.mul)               ;; x * 2

  (func $add_five (param $y i32) (result i32)
    local.get $y
    i32.const 5
    i32.add)               ;; y + 5

  (func $main_chain (param $a i32) (result i32)
    local.get $a
    call $double           ;; temp = double(a)
    call $add_five         ;; result = add_five(temp)
  )

  (export "main_chain" (func $main_chain))
)
