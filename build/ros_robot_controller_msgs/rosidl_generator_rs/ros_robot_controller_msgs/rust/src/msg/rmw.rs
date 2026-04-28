#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__BusServoState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__BusServoState__init(msg: *mut BusServoState) -> bool;
    fn ros_robot_controller_msgs__msg__BusServoState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<BusServoState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__BusServoState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<BusServoState>);
    fn ros_robot_controller_msgs__msg__BusServoState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<BusServoState>, out_seq: *mut rosidl_runtime_rs::Sequence<BusServoState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__BusServoState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BusServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub present_id: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub target_id: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub offset: rosidl_runtime_rs::Sequence<i16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub voltage: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub temperature: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position_limit: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub voltage_limit: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub max_temperature_limit: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub enable_torque: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub save_offset: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stop: rosidl_runtime_rs::Sequence<u16>,

}



impl Default for BusServoState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__BusServoState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__BusServoState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for BusServoState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__BusServoState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__BusServoState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__BusServoState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for BusServoState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for BusServoState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/BusServoState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__BusServoState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__ButtonState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__ButtonState__init(msg: *mut ButtonState) -> bool;
    fn ros_robot_controller_msgs__msg__ButtonState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ButtonState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__ButtonState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ButtonState>);
    fn ros_robot_controller_msgs__msg__ButtonState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ButtonState>, out_seq: *mut rosidl_runtime_rs::Sequence<ButtonState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__ButtonState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ButtonState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub state: u8,

}



impl Default for ButtonState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__ButtonState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__ButtonState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ButtonState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ButtonState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ButtonState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ButtonState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ButtonState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ButtonState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/ButtonState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__ButtonState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__BuzzerState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__BuzzerState__init(msg: *mut BuzzerState) -> bool;
    fn ros_robot_controller_msgs__msg__BuzzerState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<BuzzerState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__BuzzerState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<BuzzerState>);
    fn ros_robot_controller_msgs__msg__BuzzerState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<BuzzerState>, out_seq: *mut rosidl_runtime_rs::Sequence<BuzzerState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__BuzzerState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BuzzerState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub freq: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub on_time: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub off_time: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat: u16,

}



impl Default for BuzzerState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__BuzzerState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__BuzzerState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for BuzzerState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__BuzzerState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__BuzzerState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__BuzzerState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for BuzzerState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for BuzzerState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/BuzzerState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__BuzzerState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__LedState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__LedState__init(msg: *mut LedState) -> bool;
    fn ros_robot_controller_msgs__msg__LedState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<LedState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__LedState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<LedState>);
    fn ros_robot_controller_msgs__msg__LedState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<LedState>, out_seq: *mut rosidl_runtime_rs::Sequence<LedState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__LedState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct LedState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub on_time: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub off_time: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat: u16,

}



impl Default for LedState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__LedState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__LedState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for LedState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__LedState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__LedState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__LedState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for LedState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for LedState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/LedState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__LedState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__MotorState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__MotorState__init(msg: *mut MotorState) -> bool;
    fn ros_robot_controller_msgs__msg__MotorState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MotorState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__MotorState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MotorState>);
    fn ros_robot_controller_msgs__msg__MotorState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MotorState>, out_seq: *mut rosidl_runtime_rs::Sequence<MotorState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__MotorState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MotorState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rps: f64,

}



impl Default for MotorState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__MotorState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__MotorState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MotorState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__MotorState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__MotorState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__MotorState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MotorState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MotorState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/MotorState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__MotorState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__MotorsState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__MotorsState__init(msg: *mut MotorsState) -> bool;
    fn ros_robot_controller_msgs__msg__MotorsState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<MotorsState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__MotorsState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<MotorsState>);
    fn ros_robot_controller_msgs__msg__MotorsState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<MotorsState>, out_seq: *mut rosidl_runtime_rs::Sequence<MotorsState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__MotorsState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MotorsState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub data: rosidl_runtime_rs::Sequence<super::super::msg::rmw::MotorState>,

}



impl Default for MotorsState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__MotorsState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__MotorsState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for MotorsState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__MotorsState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__MotorsState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__MotorsState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for MotorsState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for MotorsState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/MotorsState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__MotorsState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__PWMServoState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__PWMServoState__init(msg: *mut PWMServoState) -> bool;
    fn ros_robot_controller_msgs__msg__PWMServoState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PWMServoState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__PWMServoState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PWMServoState>);
    fn ros_robot_controller_msgs__msg__PWMServoState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PWMServoState>, out_seq: *mut rosidl_runtime_rs::Sequence<PWMServoState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__PWMServoState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PWMServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: rosidl_runtime_rs::Sequence<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub offset: rosidl_runtime_rs::Sequence<i16>,

}



impl Default for PWMServoState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__PWMServoState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__PWMServoState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PWMServoState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__PWMServoState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__PWMServoState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__PWMServoState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PWMServoState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PWMServoState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/PWMServoState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__PWMServoState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__Sbus() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__Sbus__init(msg: *mut Sbus) -> bool;
    fn ros_robot_controller_msgs__msg__Sbus__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Sbus>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__Sbus__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Sbus>);
    fn ros_robot_controller_msgs__msg__Sbus__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Sbus>, out_seq: *mut rosidl_runtime_rs::Sequence<Sbus>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__Sbus
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Sbus {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub channel: rosidl_runtime_rs::Sequence<f32>,

}



impl Default for Sbus {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__Sbus__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__Sbus__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Sbus {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__Sbus__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__Sbus__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__Sbus__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Sbus {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Sbus where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/Sbus";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__Sbus() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__OLEDState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__OLEDState__init(msg: *mut OLEDState) -> bool;
    fn ros_robot_controller_msgs__msg__OLEDState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<OLEDState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__OLEDState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<OLEDState>);
    fn ros_robot_controller_msgs__msg__OLEDState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<OLEDState>, out_seq: *mut rosidl_runtime_rs::Sequence<OLEDState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__OLEDState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct OLEDState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub index: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub text: rosidl_runtime_rs::String,

}



impl Default for OLEDState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__OLEDState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__OLEDState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for OLEDState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__OLEDState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__OLEDState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__OLEDState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for OLEDState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for OLEDState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/OLEDState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__OLEDState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__SetBusServoState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__SetBusServoState__init(msg: *mut SetBusServoState) -> bool;
    fn ros_robot_controller_msgs__msg__SetBusServoState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<SetBusServoState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__SetBusServoState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<SetBusServoState>);
    fn ros_robot_controller_msgs__msg__SetBusServoState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<SetBusServoState>, out_seq: *mut rosidl_runtime_rs::Sequence<SetBusServoState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__SetBusServoState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SetBusServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub state: rosidl_runtime_rs::Sequence<super::super::msg::rmw::BusServoState>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub duration: f64,

}



impl Default for SetBusServoState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__SetBusServoState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__SetBusServoState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for SetBusServoState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__SetBusServoState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__SetBusServoState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__SetBusServoState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for SetBusServoState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for SetBusServoState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/SetBusServoState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__SetBusServoState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__RGBStates() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__RGBStates__init(msg: *mut RGBStates) -> bool;
    fn ros_robot_controller_msgs__msg__RGBStates__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RGBStates>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__RGBStates__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RGBStates>);
    fn ros_robot_controller_msgs__msg__RGBStates__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RGBStates>, out_seq: *mut rosidl_runtime_rs::Sequence<RGBStates>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__RGBStates
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RGBStates {

    // This member is not documented.
    #[allow(missing_docs)]
    pub states: rosidl_runtime_rs::Sequence<super::super::msg::rmw::RGBState>,

}



impl Default for RGBStates {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__RGBStates__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__RGBStates__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RGBStates {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__RGBStates__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__RGBStates__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__RGBStates__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RGBStates {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RGBStates where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/RGBStates";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__RGBStates() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__RGBState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__RGBState__init(msg: *mut RGBState) -> bool;
    fn ros_robot_controller_msgs__msg__RGBState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RGBState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__RGBState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RGBState>);
    fn ros_robot_controller_msgs__msg__RGBState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RGBState>, out_seq: *mut rosidl_runtime_rs::Sequence<RGBState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__RGBState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RGBState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub index: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub red: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub green: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub blue: u8,

}



impl Default for RGBState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__RGBState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__RGBState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RGBState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__RGBState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__RGBState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__RGBState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RGBState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RGBState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/RGBState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__RGBState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__ServoPosition() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__ServoPosition__init(msg: *mut ServoPosition) -> bool;
    fn ros_robot_controller_msgs__msg__ServoPosition__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ServoPosition>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__ServoPosition__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ServoPosition>);
    fn ros_robot_controller_msgs__msg__ServoPosition__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ServoPosition>, out_seq: *mut rosidl_runtime_rs::Sequence<ServoPosition>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__ServoPosition
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ServoPosition {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: u16,

}



impl Default for ServoPosition {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__ServoPosition__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__ServoPosition__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ServoPosition {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ServoPosition__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ServoPosition__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ServoPosition__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ServoPosition {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ServoPosition where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/ServoPosition";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__ServoPosition() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__ServosPosition() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__ServosPosition__init(msg: *mut ServosPosition) -> bool;
    fn ros_robot_controller_msgs__msg__ServosPosition__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ServosPosition>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__ServosPosition__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ServosPosition>);
    fn ros_robot_controller_msgs__msg__ServosPosition__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ServosPosition>, out_seq: *mut rosidl_runtime_rs::Sequence<ServosPosition>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__ServosPosition
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ServosPosition {

    // This member is not documented.
    #[allow(missing_docs)]
    pub duration: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: rosidl_runtime_rs::Sequence<super::super::msg::rmw::ServoPosition>,

}



impl Default for ServosPosition {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__ServosPosition__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__ServosPosition__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ServosPosition {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ServosPosition__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ServosPosition__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__ServosPosition__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ServosPosition {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ServosPosition where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/ServosPosition";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__ServosPosition() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__SetPWMServoState() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__SetPWMServoState__init(msg: *mut SetPWMServoState) -> bool;
    fn ros_robot_controller_msgs__msg__SetPWMServoState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<SetPWMServoState>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__SetPWMServoState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<SetPWMServoState>);
    fn ros_robot_controller_msgs__msg__SetPWMServoState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<SetPWMServoState>, out_seq: *mut rosidl_runtime_rs::Sequence<SetPWMServoState>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__SetPWMServoState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SetPWMServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub state: rosidl_runtime_rs::Sequence<super::super::msg::rmw::PWMServoState>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub duration: f64,

}



impl Default for SetPWMServoState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__SetPWMServoState__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__SetPWMServoState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for SetPWMServoState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__SetPWMServoState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__SetPWMServoState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__SetPWMServoState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for SetPWMServoState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for SetPWMServoState where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/SetPWMServoState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__SetPWMServoState() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__GetBusServoCmd() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__GetBusServoCmd__init(msg: *mut GetBusServoCmd) -> bool;
    fn ros_robot_controller_msgs__msg__GetBusServoCmd__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetBusServoCmd>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__GetBusServoCmd__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetBusServoCmd>);
    fn ros_robot_controller_msgs__msg__GetBusServoCmd__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetBusServoCmd>, out_seq: *mut rosidl_runtime_rs::Sequence<GetBusServoCmd>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__GetBusServoCmd
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetBusServoCmd {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_id: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_position: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_offset: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_voltage: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_temperature: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_position_limit: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_voltage_limit: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_max_temperature_limit: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_torque_state: u8,

}



impl Default for GetBusServoCmd {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__GetBusServoCmd__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__GetBusServoCmd__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetBusServoCmd {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__GetBusServoCmd__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__GetBusServoCmd__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__GetBusServoCmd__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetBusServoCmd {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetBusServoCmd where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/GetBusServoCmd";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__GetBusServoCmd() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__GetPWMServoCmd() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__msg__GetPWMServoCmd__init(msg: *mut GetPWMServoCmd) -> bool;
    fn ros_robot_controller_msgs__msg__GetPWMServoCmd__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoCmd>, size: usize) -> bool;
    fn ros_robot_controller_msgs__msg__GetPWMServoCmd__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoCmd>);
    fn ros_robot_controller_msgs__msg__GetPWMServoCmd__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetPWMServoCmd>, out_seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoCmd>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__msg__GetPWMServoCmd
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetPWMServoCmd {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_position: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub get_offset: u8,

}



impl Default for GetPWMServoCmd {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__msg__GetPWMServoCmd__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__msg__GetPWMServoCmd__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetPWMServoCmd {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__GetPWMServoCmd__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__GetPWMServoCmd__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__msg__GetPWMServoCmd__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetPWMServoCmd {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetPWMServoCmd where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/msg/GetPWMServoCmd";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__msg__GetPWMServoCmd() }
  }
}


