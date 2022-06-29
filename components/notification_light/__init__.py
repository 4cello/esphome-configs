from re import M
import esphome.codegen as cg
import esphome.config_validation as cv

CONF_COLORS = "colors"

notification_light_ns = cg.esphome_ns.namespace("notification_light")
NotificationLight = notification_light_ns.class_("NotificationLight", cg.EntityBase)


CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(NotificationLight),
    cv.Required(CONF_COLORS): cv.All(
        cv.ensure_list(cv.string_strict), cv.Length(min=1)
    )
})

def validate(config):
    raise cv.invalid(str(config[CONF_COLORS]))
    print(config[CONF_COLORS])

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])