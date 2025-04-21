(module
  (type $binary_op (func (param i32 i32) (result i32)))

  ;; 两个可选函数：加法 和 乘法
  (func $add (type $binary_op)
    (param $x i32) (param $y i32) (result i32)
    local.get $x
    local.get $y
    i32.add)

  (func $mul (type $binary_op)
    (param $x i32) (param $y i32) (result i32)
    local.get $x
    local.get $y
    i32.mul)

  ;; 函数表
  (table funcref (elem $add $mul))

  ;; 使用间接调用，根据 f_idx 选择 add 或 mul
  (func $indirect_call (param $f_idx i32) (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    local.get $f_idx
    call_indirect (type $binary_op)
  )

  (export "indirect_call" (func $indirect_call))
)
