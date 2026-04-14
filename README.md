# my-fitness-app

## <ins>Project Overview</ins>

This project is a Fitness Prototype/Mock Application designed to demonstrate full-stack engineering and DevOps automation within a public sector context.
Initially developed using MOJ branding, the project was initilised to simulate departmental transition to HMPPS identitify standards. transition involved:

<ins>Infrastructure Migration</ins>: Moving from corporate- managed environment to a stand alone, hardened architecture 
<ins>Identity Alignment</ins>: Updating application templates and assets that reflect HMPPS and compliance.
<ins>Automated Deployement</ins>: Ensuring that organisational changes can deploy across estate with zero downtime via CI/CD pipeline.

### Technical Stack 
**Backend**: Python (Flask), SQLite, Gunicorn.
**Frontend**: Nunjucks, Bootstrap.
**IaaC**: Terraform (AWS Provider).
**Infrastrcture**: AWS EC2 (Amazon Linux 2023), VPC, ELASTIC IP.
**Security**: Cloudflare Zero-Trust Tunnels, RSA 2048 SSH Key Exchange.
**Automation**: Github Actions (CI/CD)


### Future Development & Areas for improvments 

1 Frontend Enhancements (UX/UI)
  - Template Modernisation: Transition from basic bootstap to robust frameweork
  - Accessibility (WCAG): Implement full compliiance to meet public sectore accessibility standards
  - Dynamic Data Visulaisation


2 Infrastructure & Scaling 
- containerisation: Migrate the application from EC2 to containers eg AWS ECS or kubernetes (EKS)
  
    
