(module
  (type (;0;) (func (result i32)))
  (func (;0;) (type 0) (result i32)
    (local i32 i32 i32)
    i32.const 1
    local.set 0
    local.get 0
    i32.const 5
    i32.add
    local.set 1
    local.get 1
    i32.const 10
    i32.lt_s
    if  ;; label = @1
      local.get 0
      local.set 2
    else
      local.get 1
      local.set 2
    end
    i32.const 0
    return)
  (export "main" (func 0)))
