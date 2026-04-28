#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to ros_robot_controller_msgs__msg__BusServoState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BusServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub present_id: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub target_id: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub offset: Vec<i16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub voltage: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub temperature: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position_limit: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub voltage_limit: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub max_temperature_limit: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub enable_torque: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub save_offset: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stop: Vec<u16>,

}



impl Default for BusServoState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::BusServoState::default())
  }
}

impl rosidl_runtime_rs::Message for BusServoState {
  type RmwMsg = super::msg::rmw::BusServoState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        present_id: msg.present_id.into(),
        target_id: msg.target_id.into(),
        position: msg.position.into(),
        offset: msg.offset.into(),
        voltage: msg.voltage.into(),
        temperature: msg.temperature.into(),
        position_limit: msg.position_limit.into(),
        voltage_limit: msg.voltage_limit.into(),
        max_temperature_limit: msg.max_temperature_limit.into(),
        enable_torque: msg.enable_torque.into(),
        save_offset: msg.save_offset.into(),
        stop: msg.stop.into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        present_id: msg.present_id.as_slice().into(),
        target_id: msg.target_id.as_slice().into(),
        position: msg.position.as_slice().into(),
        offset: msg.offset.as_slice().into(),
        voltage: msg.voltage.as_slice().into(),
        temperature: msg.temperature.as_slice().into(),
        position_limit: msg.position_limit.as_slice().into(),
        voltage_limit: msg.voltage_limit.as_slice().into(),
        max_temperature_limit: msg.max_temperature_limit.as_slice().into(),
        enable_torque: msg.enable_torque.as_slice().into(),
        save_offset: msg.save_offset.as_slice().into(),
        stop: msg.stop.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      present_id: msg.present_id
          .into_iter()
          .collect(),
      target_id: msg.target_id
          .into_iter()
          .collect(),
      position: msg.position
          .into_iter()
          .collect(),
      offset: msg.offset
          .into_iter()
          .collect(),
      voltage: msg.voltage
          .into_iter()
          .collect(),
      temperature: msg.temperature
          .into_iter()
          .collect(),
      position_limit: msg.position_limit
          .into_iter()
          .collect(),
      voltage_limit: msg.voltage_limit
          .into_iter()
          .collect(),
      max_temperature_limit: msg.max_temperature_limit
          .into_iter()
          .collect(),
      enable_torque: msg.enable_torque
          .into_iter()
          .collect(),
      save_offset: msg.save_offset
          .into_iter()
          .collect(),
      stop: msg.stop
          .into_iter()
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__ButtonState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ButtonState::default())
  }
}

impl rosidl_runtime_rs::Message for ButtonState {
  type RmwMsg = super::msg::rmw::ButtonState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        state: msg.state,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      state: msg.state,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      state: msg.state,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__BuzzerState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::BuzzerState::default())
  }
}

impl rosidl_runtime_rs::Message for BuzzerState {
  type RmwMsg = super::msg::rmw::BuzzerState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        freq: msg.freq,
        on_time: msg.on_time,
        off_time: msg.off_time,
        repeat: msg.repeat,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      freq: msg.freq,
      on_time: msg.on_time,
      off_time: msg.off_time,
      repeat: msg.repeat,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      freq: msg.freq,
      on_time: msg.on_time,
      off_time: msg.off_time,
      repeat: msg.repeat,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__LedState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::LedState::default())
  }
}

impl rosidl_runtime_rs::Message for LedState {
  type RmwMsg = super::msg::rmw::LedState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        on_time: msg.on_time,
        off_time: msg.off_time,
        repeat: msg.repeat,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      on_time: msg.on_time,
      off_time: msg.off_time,
      repeat: msg.repeat,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      on_time: msg.on_time,
      off_time: msg.off_time,
      repeat: msg.repeat,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__MotorState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MotorState::default())
  }
}

impl rosidl_runtime_rs::Message for MotorState {
  type RmwMsg = super::msg::rmw::MotorState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        rps: msg.rps,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      rps: msg.rps,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      rps: msg.rps,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__MotorsState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MotorsState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub data: Vec<super::msg::MotorState>,

}



impl Default for MotorsState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MotorsState::default())
  }
}

impl rosidl_runtime_rs::Message for MotorsState {
  type RmwMsg = super::msg::rmw::MotorsState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        data: msg.data
          .into_iter()
          .map(|elem| super::msg::MotorState::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        data: msg.data
          .iter()
          .map(|elem| super::msg::MotorState::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      data: msg.data
          .into_iter()
          .map(super::msg::MotorState::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__PWMServoState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PWMServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub id: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: Vec<u16>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub offset: Vec<i16>,

}



impl Default for PWMServoState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::PWMServoState::default())
  }
}

impl rosidl_runtime_rs::Message for PWMServoState {
  type RmwMsg = super::msg::rmw::PWMServoState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id.into(),
        position: msg.position.into(),
        offset: msg.offset.into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id.as_slice().into(),
        position: msg.position.as_slice().into(),
        offset: msg.offset.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id
          .into_iter()
          .collect(),
      position: msg.position
          .into_iter()
          .collect(),
      offset: msg.offset
          .into_iter()
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__Sbus

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Sbus {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub channel: Vec<f32>,

}



impl Default for Sbus {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Sbus::default())
  }
}

impl rosidl_runtime_rs::Message for Sbus {
  type RmwMsg = super::msg::rmw::Sbus;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        channel: msg.channel.into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        channel: msg.channel.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      channel: msg.channel
          .into_iter()
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__OLEDState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct OLEDState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub index: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub text: std::string::String,

}



impl Default for OLEDState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::OLEDState::default())
  }
}

impl rosidl_runtime_rs::Message for OLEDState {
  type RmwMsg = super::msg::rmw::OLEDState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        index: msg.index,
        text: msg.text.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      index: msg.index,
        text: msg.text.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      index: msg.index,
      text: msg.text.to_string(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__SetBusServoState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SetBusServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub state: Vec<super::msg::BusServoState>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub duration: f64,

}



impl Default for SetBusServoState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::SetBusServoState::default())
  }
}

impl rosidl_runtime_rs::Message for SetBusServoState {
  type RmwMsg = super::msg::rmw::SetBusServoState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        state: msg.state
          .into_iter()
          .map(|elem| super::msg::BusServoState::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
        duration: msg.duration,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        state: msg.state
          .iter()
          .map(|elem| super::msg::BusServoState::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      duration: msg.duration,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      state: msg.state
          .into_iter()
          .map(super::msg::BusServoState::from_rmw_message)
          .collect(),
      duration: msg.duration,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__RGBStates

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RGBStates {

    // This member is not documented.
    #[allow(missing_docs)]
    pub states: Vec<super::msg::RGBState>,

}



impl Default for RGBStates {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::RGBStates::default())
  }
}

impl rosidl_runtime_rs::Message for RGBStates {
  type RmwMsg = super::msg::rmw::RGBStates;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        states: msg.states
          .into_iter()
          .map(|elem| super::msg::RGBState::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        states: msg.states
          .iter()
          .map(|elem| super::msg::RGBState::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      states: msg.states
          .into_iter()
          .map(super::msg::RGBState::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__RGBState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::RGBState::default())
  }
}

impl rosidl_runtime_rs::Message for RGBState {
  type RmwMsg = super::msg::rmw::RGBState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        index: msg.index,
        red: msg.red,
        green: msg.green,
        blue: msg.blue,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      index: msg.index,
      red: msg.red,
      green: msg.green,
      blue: msg.blue,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      index: msg.index,
      red: msg.red,
      green: msg.green,
      blue: msg.blue,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__ServoPosition

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ServoPosition::default())
  }
}

impl rosidl_runtime_rs::Message for ServoPosition {
  type RmwMsg = super::msg::rmw::ServoPosition;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        position: msg.position,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      position: msg.position,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      position: msg.position,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__ServosPosition

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ServosPosition {

    // This member is not documented.
    #[allow(missing_docs)]
    pub duration: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub position: Vec<super::msg::ServoPosition>,

}



impl Default for ServosPosition {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ServosPosition::default())
  }
}

impl rosidl_runtime_rs::Message for ServosPosition {
  type RmwMsg = super::msg::rmw::ServosPosition;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        duration: msg.duration,
        position: msg.position
          .into_iter()
          .map(|elem| super::msg::ServoPosition::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      duration: msg.duration,
        position: msg.position
          .iter()
          .map(|elem| super::msg::ServoPosition::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      duration: msg.duration,
      position: msg.position
          .into_iter()
          .map(super::msg::ServoPosition::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__SetPWMServoState

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SetPWMServoState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub state: Vec<super::msg::PWMServoState>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub duration: f64,

}



impl Default for SetPWMServoState {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::SetPWMServoState::default())
  }
}

impl rosidl_runtime_rs::Message for SetPWMServoState {
  type RmwMsg = super::msg::rmw::SetPWMServoState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        state: msg.state
          .into_iter()
          .map(|elem| super::msg::PWMServoState::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
        duration: msg.duration,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        state: msg.state
          .iter()
          .map(|elem| super::msg::PWMServoState::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      duration: msg.duration,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      state: msg.state
          .into_iter()
          .map(super::msg::PWMServoState::from_rmw_message)
          .collect(),
      duration: msg.duration,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__GetBusServoCmd

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::GetBusServoCmd::default())
  }
}

impl rosidl_runtime_rs::Message for GetBusServoCmd {
  type RmwMsg = super::msg::rmw::GetBusServoCmd;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        get_id: msg.get_id,
        get_position: msg.get_position,
        get_offset: msg.get_offset,
        get_voltage: msg.get_voltage,
        get_temperature: msg.get_temperature,
        get_position_limit: msg.get_position_limit,
        get_voltage_limit: msg.get_voltage_limit,
        get_max_temperature_limit: msg.get_max_temperature_limit,
        get_torque_state: msg.get_torque_state,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      get_id: msg.get_id,
      get_position: msg.get_position,
      get_offset: msg.get_offset,
      get_voltage: msg.get_voltage,
      get_temperature: msg.get_temperature,
      get_position_limit: msg.get_position_limit,
      get_voltage_limit: msg.get_voltage_limit,
      get_max_temperature_limit: msg.get_max_temperature_limit,
      get_torque_state: msg.get_torque_state,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      get_id: msg.get_id,
      get_position: msg.get_position,
      get_offset: msg.get_offset,
      get_voltage: msg.get_voltage,
      get_temperature: msg.get_temperature,
      get_position_limit: msg.get_position_limit,
      get_voltage_limit: msg.get_voltage_limit,
      get_max_temperature_limit: msg.get_max_temperature_limit,
      get_torque_state: msg.get_torque_state,
    }
  }
}


// Corresponds to ros_robot_controller_msgs__msg__GetPWMServoCmd

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::GetPWMServoCmd::default())
  }
}

impl rosidl_runtime_rs::Message for GetPWMServoCmd {
  type RmwMsg = super::msg::rmw::GetPWMServoCmd;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        id: msg.id,
        get_position: msg.get_position,
        get_offset: msg.get_offset,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      id: msg.id,
      get_position: msg.get_position,
      get_offset: msg.get_offset,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      id: msg.id,
      get_position: msg.get_position,
      get_offset: msg.get_offset,
    }
  }
}


