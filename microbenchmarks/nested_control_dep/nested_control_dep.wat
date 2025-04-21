(module
  (func $nested_control (param $x i32) (result i32)
    (local $y i32)

    local.get $x
    if
      i32.const 1
      local.set $y
      local.get $x
      i32.const 10
      i32.lt_s
      if
        i32.const 2
        local.set $y
      end
    end

    local.get $y
  )
  (export "nested_control" (func $nested_control))
)
