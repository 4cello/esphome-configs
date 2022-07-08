#pragma once

#include "esphome/components/button/button.h"

namespace esphome {
namespace notification_light {

class NotificationDebugButton : public button::Button {
 public:
  // Implements the abstract `press_action` but the `on_press` trigger already handles the press.
  void press_action() override{
    ESP_LOGI("notificationdebugbutton", "blrgblrg");
  };
};

}  // namespace template_
}  // namespace esphome