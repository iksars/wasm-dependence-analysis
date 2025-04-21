(module
  (global $g (mut i32) (i32.const 0))

  (func $set_global (param $val i32)
    local.get $val
    global.set $g          ;; 写全局变量
  )

  (func $get_global (result i32)
    global.get $g          ;; 读全局变量
  )

  (export "set_global" (func $set_global))
  (export "get_global" (func $get_global))
  (export "global_g" (global $g))
)
