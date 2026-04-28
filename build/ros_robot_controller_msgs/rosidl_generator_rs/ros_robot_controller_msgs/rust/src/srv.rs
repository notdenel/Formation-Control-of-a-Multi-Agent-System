#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to ros_robot_controller_msgs__srv__GetBusServoState_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetBusServoState_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub cmd: Vec<super::msg::GetBusServoCmd>,

}



impl Default for GetBusServoState_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetBusServoState_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GetBusServoState_Request {
  type RmwMsg = super::srv::rmw::GetBusServoState_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        cmd: msg.cmd
          .into_iter()
          .map(|elem| super::msg::GetBusServoCmd::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        cmd: msg.cmd
          .iter()
          .map(|elem| super::msg::GetBusServoCmd::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      cmd: msg.cmd
          .into_iter()
          .map(super::msg::GetBusServoCmd::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__srv__GetBusServoState_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetBusServoState_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub state: Vec<super::msg::BusServoState>,

}



impl Default for GetBusServoState_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetBusServoState_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GetBusServoState_Response {
  type RmwMsg = super::srv::rmw::GetBusServoState_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        state: msg.state
          .into_iter()
          .map(|elem| super::msg::BusServoState::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        state: msg.state
          .iter()
          .map(|elem| super::msg::BusServoState::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      state: msg.state
          .into_iter()
          .map(super::msg::BusServoState::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__srv__GetPWMServoState_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetPWMServoState_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub cmd: Vec<super::msg::GetPWMServoCmd>,

}



impl Default for GetPWMServoState_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetPWMServoState_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GetPWMServoState_Request {
  type RmwMsg = super::srv::rmw::GetPWMServoState_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        cmd: msg.cmd
          .into_iter()
          .map(|elem| super::msg::GetPWMServoCmd::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        cmd: msg.cmd
          .iter()
          .map(|elem| super::msg::GetPWMServoCmd::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      cmd: msg.cmd
          .into_iter()
          .map(super::msg::GetPWMServoCmd::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__srv__GetPWMServoState_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetPWMServoState_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub state: Vec<super::msg::PWMServoState>,

}



impl Default for GetPWMServoState_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetPWMServoState_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GetPWMServoState_Response {
  type RmwMsg = super::srv::rmw::GetPWMServoState_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        state: msg.state
          .into_iter()
          .map(|elem| super::msg::PWMServoState::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        state: msg.state
          .iter()
          .map(|elem| super::msg::PWMServoState::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      state: msg.state
          .into_iter()
          .map(super::msg::PWMServoState::from_rmw_message)
          .collect(),
    }
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


