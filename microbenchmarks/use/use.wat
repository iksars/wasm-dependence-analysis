(module
  (memory 1) ;; 1页(64KiB)线性内存
  (global $g0 (mut i32) (i32.const 0)) ;; 可变全局变量
  (func $compute (param $x i32) (param $y i32) (result i32)
    (local $z i32)
    ;; 栈计算依赖
    local.get $x
    local.get $y
    i32.add  ;; $z = x + y
    local.set $z ;; 存入局部变量 z

    ;; 线性内存操作依赖
    local.get $z
    i32.const 100
    i32.store  ;; mem[100] = z

    i32.const 100
    i32.load    ;; 取回 mem[100]

    ;; 控制流依赖 (if 语句)
    if (result i32)
      i32.const 1
    else
      i32.const 0
    end
  )

  ;; 递归函数 (loop 依赖)
  (func $factorial (param $n i32) (result i32)
    (local $res i32)
    i32.const 10
    local.set $n
    local.get $n
    i32.const 1
    i32.le_s  ;; if n <= 1
    if (result i32)
      i32.const 1
    else
      local.get $n
      local.get $n
      i32.const 1
      i32.sub
      call $factorial
      i32.mul
    end
  )

  (export "compute" (func $compute))
  (export "factorial" (func $factorial))
  (export "memory" (memory 0))
)
