#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetBusServoState_Request() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__srv__GetBusServoState_Request__init(msg: *mut GetBusServoState_Request) -> bool;
    fn ros_robot_controller_msgs__srv__GetBusServoState_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetBusServoState_Request>, size: usize) -> bool;
    fn ros_robot_controller_msgs__srv__GetBusServoState_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetBusServoState_Request>);
    fn ros_robot_controller_msgs__srv__GetBusServoState_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetBusServoState_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GetBusServoState_Request>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__srv__GetBusServoState_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetBusServoState_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub cmd: rosidl_runtime_rs::Sequence<super::super::msg::rmw::GetBusServoCmd>,

}



impl Default for GetBusServoState_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__srv__GetBusServoState_Request__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__srv__GetBusServoState_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetBusServoState_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetBusServoState_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetBusServoState_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetBusServoState_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetBusServoState_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetBusServoState_Request where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/srv/GetBusServoState_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetBusServoState_Request() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetBusServoState_Response() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__srv__GetBusServoState_Response__init(msg: *mut GetBusServoState_Response) -> bool;
    fn ros_robot_controller_msgs__srv__GetBusServoState_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetBusServoState_Response>, size: usize) -> bool;
    fn ros_robot_controller_msgs__srv__GetBusServoState_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetBusServoState_Response>);
    fn ros_robot_controller_msgs__srv__GetBusServoState_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetBusServoState_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GetBusServoState_Response>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__srv__GetBusServoState_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetBusServoState_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub state: rosidl_runtime_rs::Sequence<super::super::msg::rmw::BusServoState>,

}



impl Default for GetBusServoState_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__srv__GetBusServoState_Response__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__srv__GetBusServoState_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetBusServoState_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetBusServoState_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetBusServoState_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetBusServoState_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetBusServoState_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetBusServoState_Response where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/srv/GetBusServoState_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetBusServoState_Response() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetPWMServoState_Request() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Request__init(msg: *mut GetPWMServoState_Request) -> bool;
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoState_Request>, size: usize) -> bool;
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoState_Request>);
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetPWMServoState_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoState_Request>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__srv__GetPWMServoState_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetPWMServoState_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub cmd: rosidl_runtime_rs::Sequence<super::super::msg::rmw::GetPWMServoCmd>,

}



impl Default for GetPWMServoState_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__srv__GetPWMServoState_Request__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__srv__GetPWMServoState_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetPWMServoState_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetPWMServoState_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetPWMServoState_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetPWMServoState_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetPWMServoState_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetPWMServoState_Request where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/srv/GetPWMServoState_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetPWMServoState_Request() }
  }
}


#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetPWMServoState_Response() -> *const std::ffi::c_void;
}

#[link(name = "ros_robot_controller_msgs__rosidl_generator_c")]
extern "C" {
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Response__init(msg: *mut GetPWMServoState_Response) -> bool;
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoState_Response>, size: usize) -> bool;
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoState_Response>);
    fn ros_robot_controller_msgs__srv__GetPWMServoState_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetPWMServoState_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GetPWMServoState_Response>) -> bool;
}

// Corresponds to ros_robot_controller_msgs__srv__GetPWMServoState_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetPWMServoState_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub state: rosidl_runtime_rs::Sequence<super::super::msg::rmw::PWMServoState>,

}



impl Default for GetPWMServoState_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !ros_robot_controller_msgs__srv__GetPWMServoState_Response__init(&mut msg as *mut _) {
        panic!("Call to ros_robot_controller_msgs__srv__GetPWMServoState_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetPWMServoState_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetPWMServoState_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetPWMServoState_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { ros_robot_controller_msgs__srv__GetPWMServoState_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetPWMServoState_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetPWMServoState_Response where Self: Sized {
  const TYPE_NAME: &'static str = "ros_robot_controller_msgs/srv/GetPWMServoState_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__ros_robot_controller_msgs__srv__GetPWMServoState_Response() }
  }
}






#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__ros_robot_controller_msgs__srv__GetBusServoState() -> *const std::ffi::c_void;
}

// Corresponds to ros_robot_controller_msgs__srv__GetBusServoState
#[allow(missing_docs, non_camel_case_types)]
pub struct GetBusServoState;

impl rosidl_runtime_rs::Service for GetBusServoState {
    type Request = GetBusServoState_Request;
    type Response = GetBusServoState_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__ros_robot_controller_msgs__srv__GetBusServoState() }
    }
}




#[link(name = "ros_robot_controller_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__ros_robot_controller_msgs__srv__GetPWMServoState() -> *const std::ffi::c_void;
}

// Corresponds to ros_robot_controller_msgs__srv__GetPWMServoState
#[allow(missing_docs, non_camel_case_types)]
pub struct GetPWMServoState;

impl rosidl_runtime_rs::Service for GetPWMServoState {
    type Request = GetPWMServoState_Request;
    type Response = GetPWMServoState_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__ros_robot_controller_msgs__srv__GetPWMServoState() }
    }
}


