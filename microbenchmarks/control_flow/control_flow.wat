(module
  (func $control_flow (param $x i32) (result i32)
    (local $sum i32)
    (local $i i32)

    i32.const 0
    local.set $sum
    i32.const 0
    local.set $i

    block $exit
      loop $loop
        local.get $i
        local.get $x
        i32.ge_s
        br_if $exit        ;; if i >= x then break

        local.get $sum
        local.get $i
        i32.add
        local.set $sum     ;; sum += i

        local.get $i
        i32.const 1
        i32.add
        local.set $i       ;; i++

        br $loop
      end
    end

    local.get $sum
  )

  (export "control_flow" (func $control_flow))
)
