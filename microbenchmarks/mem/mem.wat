(module
  (memory 1)

  (func $mem (param $addr i32) (param $val i32) (result i32)
    local.get $addr
    local.get $val
    i32.store            ;; mem[addr] = val

    local.get $addr
    i32.load             ;; return mem[addr]
  )

  (export "mem" (func $mem))
  (export "memory" (memory 0))
)
