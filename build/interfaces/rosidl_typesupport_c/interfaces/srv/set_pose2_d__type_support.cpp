// generated from rosidl_typesupport_c/resource/idl__type_support.cpp.em
// with input from interfaces:srv/SetPose2D.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "interfaces/srv/detail/set_pose2_d__struct.h"
#include "interfaces/srv/detail/set_pose2_d__type_support.h"
#include "interfaces/srv/detail/set_pose2_d__functions.h"
#include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/message_type_support_dispatch.h"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_c/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace interfaces
{

namespace srv
{

namespace rosidl_typesupport_c
{

typedef struct _SetPose2D_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _SetPose2D_Request_type_support_ids_t;

static const _SetPose2D_Request_type_support_ids_t _SetPose2D_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _SetPose2D_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _SetPose2D_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _SetPose2D_Request_type_support_symbol_names_t _SetPose2D_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, interfaces, srv, SetPose2D_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces, srv, SetPose2D_Request)),
  }
};

typedef struct _SetPose2D_Request_type_support_data_t
{
  void * data[2];
} _SetPose2D_Request_type_support_data_t;

static _SetPose2D_Request_type_support_data_t _SetPose2D_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _SetPose2D_Request_message_typesupport_map = {
  2,
  "interfaces",
  &_SetPose2D_Request_message_typesupport_ids.typesupport_identifier[0],
  &_SetPose2D_Request_message_typesupport_symbol_names.symbol_name[0],
  &_SetPose2D_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t SetPose2D_Request_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_SetPose2D_Request_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &interfaces__srv__SetPose2D_Request__get_type_hash,
  &interfaces__srv__SetPose2D_Request__get_type_description,
  &interfaces__srv__SetPose2D_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace srv

}  // namespace interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, interfaces, srv, SetPose2D_Request)() {
  return &::interfaces::srv::rosidl_typesupport_c::SetPose2D_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__struct.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__type_support.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces
{

namespace srv
{

namespace rosidl_typesupport_c
{

typedef struct _SetPose2D_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _SetPose2D_Response_type_support_ids_t;

static const _SetPose2D_Response_type_support_ids_t _SetPose2D_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _SetPose2D_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _SetPose2D_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _SetPose2D_Response_type_support_symbol_names_t _SetPose2D_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, interfaces, srv, SetPose2D_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces, srv, SetPose2D_Response)),
  }
};

typedef struct _SetPose2D_Response_type_support_data_t
{
  void * data[2];
} _SetPose2D_Response_type_support_data_t;

static _SetPose2D_Response_type_support_data_t _SetPose2D_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _SetPose2D_Response_message_typesupport_map = {
  2,
  "interfaces",
  &_SetPose2D_Response_message_typesupport_ids.typesupport_identifier[0],
  &_SetPose2D_Response_message_typesupport_symbol_names.symbol_name[0],
  &_SetPose2D_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t SetPose2D_Response_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_SetPose2D_Response_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &interfaces__srv__SetPose2D_Response__get_type_hash,
  &interfaces__srv__SetPose2D_Response__get_type_description,
  &interfaces__srv__SetPose2D_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace srv

}  // namespace interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, interfaces, srv, SetPose2D_Response)() {
  return &::interfaces::srv::rosidl_typesupport_c::SetPose2D_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__struct.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__type_support.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace interfaces
{

namespace srv
{

namespace rosidl_typesupport_c
{

typedef struct _SetPose2D_Event_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _SetPose2D_Event_type_support_ids_t;

static const _SetPose2D_Event_type_support_ids_t _SetPose2D_Event_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _SetPose2D_Event_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _SetPose2D_Event_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _SetPose2D_Event_type_support_symbol_names_t _SetPose2D_Event_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, interfaces, srv, SetPose2D_Event)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces, srv, SetPose2D_Event)),
  }
};

typedef struct _SetPose2D_Event_type_support_data_t
{
  void * data[2];
} _SetPose2D_Event_type_support_data_t;

static _SetPose2D_Event_type_support_data_t _SetPose2D_Event_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _SetPose2D_Event_message_typesupport_map = {
  2,
  "interfaces",
  &_SetPose2D_Event_message_typesupport_ids.typesupport_identifier[0],
  &_SetPose2D_Event_message_typesupport_symbol_names.symbol_name[0],
  &_SetPose2D_Event_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t SetPose2D_Event_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_SetPose2D_Event_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &interfaces__srv__SetPose2D_Event__get_type_hash,
  &interfaces__srv__SetPose2D_Event__get_type_description,
  &interfaces__srv__SetPose2D_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace srv

}  // namespace interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, interfaces, srv, SetPose2D_Event)() {
  return &::interfaces::srv::rosidl_typesupport_c::SetPose2D_Event_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "interfaces/srv/detail/set_pose2_d__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/service_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
#include "service_msgs/msg/service_event_info.h"
#include "builtin_interfaces/msg/time.h"

namespace interfaces
{

namespace srv
{

namespace rosidl_typesupport_c
{
typedef struct _SetPose2D_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _SetPose2D_type_support_ids_t;

static const _SetPose2D_type_support_ids_t _SetPose2D_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _SetPose2D_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _SetPose2D_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _SetPose2D_type_support_symbol_names_t _SetPose2D_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, interfaces, srv, SetPose2D)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces, srv, SetPose2D)),
  }
};

typedef struct _SetPose2D_type_support_data_t
{
  void * data[2];
} _SetPose2D_type_support_data_t;

static _SetPose2D_type_support_data_t _SetPose2D_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _SetPose2D_service_typesupport_map = {
  2,
  "interfaces",
  &_SetPose2D_service_typesupport_ids.typesupport_identifier[0],
  &_SetPose2D_service_typesupport_symbol_names.symbol_name[0],
  &_SetPose2D_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t SetPose2D_service_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_SetPose2D_service_typesupport_map),
  rosidl_typesupport_c__get_service_typesupport_handle_function,
  &SetPose2D_Request_message_type_support_handle,
  &SetPose2D_Response_message_type_support_handle,
  &SetPose2D_Event_message_type_support_handle,
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_CREATE_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    interfaces,
    srv,
    SetPose2D
  ),
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_DESTROY_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    interfaces,
    srv,
    SetPose2D
  ),
  &interfaces__srv__SetPose2D__get_type_hash,
  &interfaces__srv__SetPose2D__get_type_description,
  &interfaces__srv__SetPose2D__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace srv

}  // namespace interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_c, interfaces, srv, SetPose2D)() {
  return &::interfaces::srv::rosidl_typesupport_c::SetPose2D_service_type_support_handle;
}

#ifdef __cplusplus
}
#endif
