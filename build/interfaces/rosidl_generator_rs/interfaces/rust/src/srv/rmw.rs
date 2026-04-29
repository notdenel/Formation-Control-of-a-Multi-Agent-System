#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces__srv__SetPose2D_Request() -> *const std::ffi::c_void;
}

#[link(name = "interfaces__rosidl_generator_c")]
extern "C" {
    fn interfaces__srv__SetPose2D_Request__init(msg: *mut SetPose2D_Request) -> bool;
    fn interfaces__srv__SetPose2D_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<SetPose2D_Request>, size: usize) -> bool;
    fn interfaces__srv__SetPose2D_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<SetPose2D_Request>);
    fn interfaces__srv__SetPose2D_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<SetPose2D_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<SetPose2D_Request>) -> bool;
}

// Corresponds to interfaces__srv__SetPose2D_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SetPose2D_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub data: geometry_msgs::msg::rmw::Pose2D,

}



impl Default for SetPose2D_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces__srv__SetPose2D_Request__init(&mut msg as *mut _) {
        panic!("Call to interfaces__srv__SetPose2D_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for SetPose2D_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces__srv__SetPose2D_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces__srv__SetPose2D_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces__srv__SetPose2D_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for SetPose2D_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for SetPose2D_Request where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces/srv/SetPose2D_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces__srv__SetPose2D_Request() }
  }
}


#[link(name = "interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__interfaces__srv__SetPose2D_Response() -> *const std::ffi::c_void;
}

#[link(name = "interfaces__rosidl_generator_c")]
extern "C" {
    fn interfaces__srv__SetPose2D_Response__init(msg: *mut SetPose2D_Response) -> bool;
    fn interfaces__srv__SetPose2D_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<SetPose2D_Response>, size: usize) -> bool;
    fn interfaces__srv__SetPose2D_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<SetPose2D_Response>);
    fn interfaces__srv__SetPose2D_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<SetPose2D_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<SetPose2D_Response>) -> bool;
}

// Corresponds to interfaces__srv__SetPose2D_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SetPose2D_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for SetPose2D_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !interfaces__srv__SetPose2D_Response__init(&mut msg as *mut _) {
        panic!("Call to interfaces__srv__SetPose2D_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for SetPose2D_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces__srv__SetPose2D_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces__srv__SetPose2D_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { interfaces__srv__SetPose2D_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for SetPose2D_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for SetPose2D_Response where Self: Sized {
  const TYPE_NAME: &'static str = "interfaces/srv/SetPose2D_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__interfaces__srv__SetPose2D_Response() }
  }
}






#[link(name = "interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__interfaces__srv__SetPose2D() -> *const std::ffi::c_void;
}

// Corresponds to interfaces__srv__SetPose2D
#[allow(missing_docs, non_camel_case_types)]
pub struct SetPose2D;

impl rosidl_runtime_rs::Service for SetPose2D {
    type Request = SetPose2D_Request;
    type Response = SetPose2D_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__interfaces__srv__SetPose2D() }
    }
}


