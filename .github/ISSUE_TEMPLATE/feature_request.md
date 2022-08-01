name: Feature request
description: File a bug report
title: "[Enhancement]: "
labels: ["enhancement"] 
assignees:
  - octocat
body:
  - type: textarea
    id: What is it, you request?
    attributes:
      label: Proposal
      value: "I request a feature..."
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: Version
      description: What version do you want this in?
    validations:
      required: false
