(module
  (func $stack_and_local (param $a i32) (param $b i32) (result i32)
    (local $tmp1 i32)
    (local $tmp2 i32)

    local.get $a
    local.get $b
    i32.mul          ;; $tmp1 = a * b
    local.set $tmp1

    local.get $tmp1
    i32.const 10
    i32.add          ;; $tmp2 = tmp1 + 10
    local.set $tmp2

    local.get $tmp2
  )
  (export "stack_and_local" (func $stack_and_local))
)
