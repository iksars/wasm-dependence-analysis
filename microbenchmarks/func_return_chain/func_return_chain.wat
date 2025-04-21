(module
  (func $generate (param $x i32) (result i32)
    local.get $x
    i32.const 3
    i32.add)

  (func $consume (param $input i32) (result i32)
    local.get $input
    i32.const 4
    i32.mul)

  (func $chain_use (param $seed i32) (result i32)
    local.get $seed
    call $generate       ;; gen = seed + 3
    call $consume        ;; result = gen * 4
  )

  (export "chain_use" (func $chain_use))
)
