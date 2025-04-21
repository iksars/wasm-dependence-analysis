(module
    (type (;0;) (func (param i32) (result i32)))
    (type (;1;) (func (result i32)))
    (type (;2;) (func (param i32) (param i32) (result i32)))
    (type (;3;) (func))

    (import "a" "f0" (func $f0 (type 0)))
    (import "a" "f2" (func $f2 (type 2)))
    (import "a" "f3" (func $f3 (type 3)))

    (func (;0;) (type 1)
    (local $x i32)
    (local $y i32)
    i32.const 5
    local.set $x    ;; x = 5
    i32.const 2
    local.set $y    ;; y = 2
    call $f3        ;; f3()
    local.get $y
    call $f0        ;; tmp =  f0(y)
    local.get $x
    call $f2        ;; ret = f2(x, tmp)
    )

    (export "call_import" (func 0))
)