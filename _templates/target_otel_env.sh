# Source this file in a terminal before launching CLI harnesses in the target ICM workspace:
#   source .otel/phoenix.env
export PHOENIX_ENDPOINT="http://localhost:6006"
export PHOENIX_PROJECT="__PROJECT_NAME__"
export PHOENIX_PROJECT_NAME="__PROJECT_NAME__"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:6006"
# Uncomment for verbose hook diagnostics:
# export ARIZE_VERBOSE="true"
