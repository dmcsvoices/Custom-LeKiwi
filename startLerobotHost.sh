#!/bin/bash

# LeRobot Host Configuration
# Usage: ./startLerobotHost.sh [HOST_CONFIG] [CALIBRATION_FILE] [CALIBRATION_DIR]
# Example: ./startLerobotHost.sh ./lekiwi_host_config.json ./my_lekiwi.json ~/lerobot

HOST_CONFIG="${1:-./lekiwi_host_config.json}"
CALIBRATION_FILE="${2:-./my_lekiwi.json}"
CALIBRATION_DIR="${3:-~/lerobot}"

# Expand tilde in path
CALIBRATION_DIR="${CALIBRATION_DIR/#\~/$HOME}"

# Defaults for generating config if files don't exist
ROBOT_ID="my_lekiwi"
USE_DUAL_BOARDS="true"
ARM_PORT="/dev/ttyACM1"
BASE_PORT="/dev/ttyACM0"
CONNECTION_TIME_S="7200"

PORT_ZMQ_CMD="5555"
PORT_ZMQ_OBSERVATIONS="5556"

# Check if calibration file exists
if [ ! -f "$CALIBRATION_FILE" ]; then
  echo "Error: Calibration file not found: $CALIBRATION_FILE"
  echo "Usage: ./startLerobotHost.sh [HOST_CONFIG] [CALIBRATION_FILE] [CALIBRATION_DIR]"
  exit 1
fi

# Create calibration directory if needed and copy calibration file
mkdir -p "$CALIBRATION_DIR"
if [ "$(cd $(dirname "$CALIBRATION_FILE") && pwd)/$(basename "$CALIBRATION_FILE")" != "$(cd "$CALIBRATION_DIR" && pwd)/$ROBOT_ID.json" ]; then
  cp "$CALIBRATION_FILE" "$CALIBRATION_DIR/$ROBOT_ID.json"
fi
echo "Using calibration: $CALIBRATION_DIR/$ROBOT_ID.json"

# Check if host config exists, generate if not
if [ ! -f "$HOST_CONFIG" ]; then
  echo "Host config not found: $HOST_CONFIG"
  echo "Creating host config..."

  cat > "$HOST_CONFIG" << EOF
{
  "robot": {
    "id": "$ROBOT_ID",
    "calibration_dir": "$CALIBRATION_DIR",
    "use_dual_boards": $USE_DUAL_BOARDS,
    "arm_port": "$ARM_PORT",
    "base_port": "$BASE_PORT"
  },
  "host": {
    "connection_time_s": $CONNECTION_TIME_S,
    "port_zmq_cmd": $PORT_ZMQ_CMD,
    "port_zmq_observations": $PORT_ZMQ_OBSERVATIONS
  }
}
EOF
  echo "Created: $HOST_CONFIG"
fi

echo "Using host config: $HOST_CONFIG"
echo "Running LeRobot Host..."

# Run with host config (calibration will be auto-loaded from calibration_dir)
python -m lerobot.robots.lekiwi.lekiwi_host --config_path "$HOST_CONFIG"
