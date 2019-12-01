aws cloudformation delete-stack --stack-name jenkins
aws cloudformation wait stack-delete-complete --stack-name jenkins
python jenkins-cf-template.py > jenkins-cf.template
aws cloudformation create-stack --capabilities CAPABILITY_IAM --stack-name jenkins --template-body file://jenkins-cf.template --parameters ParameterKey=KeyPair,ParameterValue=EffectiveDevOpsAWS
aws cloudformation wait stack-create-complete --stack-name jenkins
aws cloudformation describe-stacks --stack-name jenkins --query 'Stacks[0].Outputs[0]'
aws cloudformation describe-stacks
