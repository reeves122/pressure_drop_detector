
variable "name" {
  default = "pressure_drop_detector"
}

variable "zip_file" {
  default = "package.zip"
}

variable "run_interval_hours" {
  default = 6
}

provider "aws" {
  region     = "us-east-1"
}

resource "aws_iam_role" "role" {
  name = "${var.name}-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_lambda_function" "function" {
  filename         = "${var.zip_file}"
  function_name    = "${var.name}"
  role             = "${aws_iam_role.role.arn}"
  handler          = "pressure_drop_detector.lambda_handler"
  source_code_hash = "${base64sha256(file("${var.zip_file}"))}"
  runtime          = "python3.7"

  environment {
    variables = {
      LOCATION = "${var.location}"
      API_KEY  = "${var.api_key}"
    }
  }
}

resource "aws_cloudwatch_event_rule" "event_rule" {
    name = "${var.name}-every-${var.run_interval_hours}-hours"
    schedule_expression = "rate(${var.run_interval_hours} hours)"
}

resource "aws_cloudwatch_event_target" "event_target" {
    rule = "${aws_cloudwatch_event_rule.event_rule.name}"
    arn = "${aws_lambda_function.function.arn}"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check_foo" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = "${aws_lambda_function.function.function_name}"
    principal = "events.amazonaws.com"
    source_arn = "${aws_cloudwatch_event_rule.event_rule.arn}"
}