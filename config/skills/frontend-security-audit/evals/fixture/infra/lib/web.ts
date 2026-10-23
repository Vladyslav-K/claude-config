// INTENTIONALLY VULNERABLE — test fixture for scan.mjs. Never copy into a real app.
import { Peer, Port, type SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

export function openSsh(sg: SecurityGroup) {
  sg.addIngressRule(Peer.anyIpv4(), Port.tcp(22), 'ssh');
}

export const decryptAnyKey = new PolicyStatement({
  actions: ['kms:Decrypt'],
  resources: ['*'],
});
