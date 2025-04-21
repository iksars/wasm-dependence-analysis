(module
  (func $stack_and_local_with_float (param $a f64) (param $b f64) (result f64)
    (local $tmp1 f64)
    (local $tmp2 f64)

    local.get $a
    local.get $b
    f64.mul          ;; $tmp1 = a * b
    local.set $tmp1

    local.get $tmp1
    f64.const 10.0
    f64.add          ;; $tmp2 = tmp1 + 10
    local.set $tmp2

    local.get $tmp2
  )
  (export "stack_and_local_with_float" (func $stack_and_local_with_float))
)
