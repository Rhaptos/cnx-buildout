#!/bin/bash
echo "user user1 user1 firstname1 lastname1 useremail1@localhost.net 
user user2 user2 firstname2 lastname2 useremail2@localhost.net
user user3 user3 firstname3 lastname3 useremail3@localhost.net
org siyavula siyavula siya-firstname siya-lastname siya-email@localhost.net
org org1 org1 'org1 name' org1-name orgemail1@localhost.net
org org2 org2 'org2 name' org2-name orgemail2@localhost.net
manager manager1 manager1 managerfirstname1 managerlastname1 manageremail1@localhost.net" | bin/instance run scripts/addRhaptosUser.zctl
