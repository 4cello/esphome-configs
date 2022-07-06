import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID, CONF_PLATFORM
)
from esphome.components import (
    button
)
from esphome.components.mqtt import MQTTMessageTrigger
from esphome.components.button import button_ns, ButtonPressTrigger
from esphome.components.globals import GlobalsComponent
from esphome.components.template import template_ns
from esphome.core import CORE, Lambda, ID
from esphome.cpp_generator import MockObjClass
import esphome.automation as automation

from matplotlib import colors

DEPENDENCIES = [ "mqtt" ]
AUTO_LOAD = [ "button", "template" ]

CONF_COLORS = "colors"
CONF_COLOR_NAME = "color"
CONF_BUTTON_TRIGGER_ID = "button_trigger_id"
CONF_MQTT_TRIGGER_ID = "mqtt_trigger_id"

CONF_GLOBAL_COLORS_ID = "global_colors_id"
CONF_GLOBAL_PENDING_ID = "global_pending_id"

notification_light_ns = cg.esphome_ns.namespace("notification_light")
NotificationLight = notification_light_ns.class_("NotificationLight", cg.EntityBase)


CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(NotificationLight),
    cv.GenerateID(CONF_GLOBAL_COLORS_ID): cv.declare_id(GlobalsComponent),
    cv.GenerateID(CONF_GLOBAL_PENDING_ID): cv.declare_id(GlobalsComponent),
    cv.Required(CONF_COLORS): cv.All(
        cv.ensure_list(
            cv.Schema({
                cv.GenerateID(CONF_MQTT_TRIGGER_ID): cv.declare_id(MQTTMessageTrigger),
                cv.GenerateID(CONF_BUTTON_TRIGGER_ID): cv.declare_id(ButtonPressTrigger),
                cv.Required(CONF_COLOR_NAME): cv.string_strict
            })
        ), cv.Length(min=1)
    )
})

async def generate_global(id, type_str, initial_value):
    type_ = cg.RawExpression(type_str)
    template_args = cg.TemplateArguments(type_)

    type = GlobalsComponent
    res_type = type.template(template_args)

    initial_value = cg.RawExpression(initial_value)

    rhs = type.new(template_args, initial_value)
    glob = cg.Pvariable(id, rhs, res_type)

    config = {}
    await cg.register_component(glob, config)
    return None

async def generate_globals(config, colors):
    color_count = len(colors)
    await generate_global(
        config[CONF_GLOBAL_COLORS_ID],
        f"Color[{color_count}]",
        "{" + f",".join([f"Color{c}" for c in colors]) + "}"
    )
    await generate_global(
        config[CONF_GLOBAL_PENDING_ID],
        f"time_t[{color_count}]",
        "{" + ",".join(["0" for _ in range(color_count)]) + "}"
    )



async def generate_button(color_name, trigger_id):
    mqttid = ID("mqtt_mqttclientcomponent", False, MockObjClass(base="mqtt::MQTTClientComponent", parents=[
        MockObjClass(base="Component", parents=[])
    ]))

    id = f"template__templatebutton_{color_name}"
    publish_id = ID(f"mqtt_mqttpublishaction_{color_name}", True, MockObjClass(
        base="mqtt::MQTTPublishAction", parents=[MockObjClass(base="Action", parents=[])]
    ), False)
    conf = {
        "platform": "template",
        "id": ID(id, True, MockObjClass(base="template_::TemplateButton", parents=[
            MockObjClass(base="button::Button", parents=[MockObjClass(base="EntityBase", parents=[])]),
            MockObjClass(base="EntityBase", parents=[])
        ]), False),
        "name": f"Test {color_name.upper()} notification",
        "disabled_by_default": False,
        "on_press": [{
            "then": [{
                "mqtt.publish": {
                    "topic": f"esphome/notification-test/notify/{color_name}",
                    "payload": Lambda("char buf[32]; \nreturn itoa(id(sntp_time).now().timestamp + 30, buf, 10);"),
                    "id": mqttid,
                    "qos": 0,
                    "retain": False
                },
                "type_id": publish_id
            }],
            "automation_id": ID(f"automation_button_{color_name}", True, MockObjClass(base="Automation", parents=[]), False),
            "trigger_id": trigger_id
        }]
    }
    btn = await button.new_button(conf)
    # TODO:
    """
        automation->add_actions({mqtt_mqttpublishaction});
        mqtt_mqttbuttoncomponent = new mqtt::MQTTButtonComponent(template__templatebutton);
        mqtt_mqttbuttoncomponent->set_component_source("mqtt");
        App.register_component(mqtt_mqttbuttoncomponent);
    """
    return btn

async def subscribe_mqtt(color_name, trigger_id):
    trig = cg.new_Pvariable(trigger_id, f"esphome/notification-test/notify/{color_name}")
    cg.add(trig.set_qos(0))
    conf = {
        "automation_id": ID(f"automation_mqttsub_{color_name}", True, MockObjClass(base="Automation", parents=[]), False),
        "then": [
            {
                "logger.log": {
                    "level": "INFO",
                    "format": f"Received new timestamp for color {color_name}: %s",
                    "args": [Lambda("x.c_str()")],
                    "tag": "main"
                },
                "type_id": ID(f"lambdaaction_mqttsub_log_{color_name}", True, MockObjClass(
                    base="LambdaAction", parents=[MockObjClass(base="Action", parents=[])]
                ), False)
            },
            {
                "lambda": Lambda("""time_t end = atoll(x.c_str());
                    time_t old = id(pending_notifications)[0];
                    if (end > old)
                        id(pending_notifications)[0] = end;"""),
                "type_id": ID(f"lambdaaction_mqttsub_{color_name}", True, MockObjClass(
                    base="LambdaAction", parents=[MockObjClass(base="Action", parents=[])]
                ), False)
            }
        ]
    }
    await cg.register_component(trig, conf)
    await automation.build_automation(trig, [(cg.std_string, "x")], conf)
    return None

async def to_code(config):
    cg.add_global(template_ns.using)
    #cg.add_define("USE_TEMPLATE")

    ctempl = CORE.config["template"]
    if isinstance(ctempl, dict): 
        ctempl[CONF_PLATFORM]= "button"
    elif isinstance(ctempl, list):
        ctempl.append[{CONF_PLATFORM: "button"}]

    cg.add_global(button_ns.using)
    cg.add_define("USE_BUTTON")

    rgb_colors = [tuple(int(i*255) for i in colors.to_rgb(c[CONF_COLOR_NAME].lower())) for c in config[CONF_COLORS]]
    await generate_globals(config, rgb_colors)
    for c in config[CONF_COLORS]:
        color_name = c[CONF_COLOR_NAME].lower()
        await generate_button(color_name, c[CONF_BUTTON_TRIGGER_ID])
        await subscribe_mqtt(color_name, c[CONF_MQTT_TRIGGER_ID])