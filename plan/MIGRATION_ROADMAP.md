# Migration Roadmap: Current → Ideal Tech Stack

**Document Version:** 1.0  
**Date:** December 2024  
**Timeline:** 18 months phased migration  
**Objective:** Transform HadadaHealth from functional MVP to enterprise healthcare platform  

---

## Executive Summary

This roadmap provides a systematic migration from the current FastAPI/SQLite stack to an enterprise-ready PostgreSQL/React/AWS architecture. The approach prioritizes **zero downtime**, **data integrity**, and **continuous value delivery** throughout the transformation.

**Migration Philosophy:**
- ✅ **Incremental changes** - no big-bang rewrites
- ✅ **Parallel systems** - run old and new side-by-side
- ✅ **Feature flags** - gradual rollout of new components
- ✅ **Data safety first** - comprehensive backups and rollback plans

---

## Current State Analysis

### **Existing Architecture (Working Foundation)**
```
FastAPI + Python 3.12
├── SQLite direct queries (2800+ line main.py)
├── Jinja2 templates + vanilla JavaScript
├── Session-based authentication (bcrypt)
├── Local file storage
├── Render deployment
└── No automated testing
```

### **Key Strengths to Preserve**
- ✅ **Modular business logic** - well-organized modules/
- ✅ **Comprehensive validation** - Pydantic models
- ✅ **Security foundation** - recent hardening completed
- ✅ **Healthcare domain knowledge** - outcome measures, billing logic
- ✅ **Working user base** - established workflows

### **Critical Migration Constraints**
- **Zero data loss** - patient records are irreplaceable
- **Minimal downtime** - healthcare operations cannot stop
- **Regulatory compliance** - POPIA requirements throughout
- **User training** - gradual UX changes to minimize disruption

---

## 18-Month Migration Timeline

## **Phase 1: Foundation & Safety (Months 1-3)**
*Priority: Establish testing safety net and database reliability*

### **Month 1: Testing Infrastructure**
**Objective**: Enable confident changes with comprehensive test coverage

**Week 1-2: Test Framework Setup**
```bash
# Add to requirements.txt
pytest==8.0+
pytest-asyncio==0.23+
pytest-cov==4.0+
httpx==0.27.2  # Already present
factory-boy==3.3+  # Test data generation
```

**Implementation Tasks:**
- [ ] Set up pytest configuration and structure
- [ ] Create test database fixtures with sample healthcare data
- [ ] Write integration tests for critical user journeys:
  - Patient creation and management
  - Appointment booking and treatment notes
  - Billing and invoice generation
  - User authentication and permissions
- [ ] Establish 80% code coverage baseline
- [ ] Add automated test runs to git hooks

**Success Criteria:**
- All critical workflows covered by integration tests
- 80%+ code coverage across business logic modules
- Test suite runs in <2 minutes
- Zero false positives in test results

**Week 3-4: Database Migration Prep**
- [ ] Create complete database schema documentation
- [ ] Set up automated database backups (daily + pre-change)
- [ ] Document all existing queries and their business purposes
- [ ] Create data validation scripts to verify migration integrity

### **Month 2: Database Migration to PostgreSQL**
**Objective**: Migrate from SQLite to PostgreSQL with zero data loss

**Week 1: PostgreSQL Infrastructure**
```bash
# Add to requirements.txt
sqlalchemy==2.0+
alembic==1.13+
asyncpg==0.29+
psycopg2-binary==2.9+  # Fallback sync driver
```

**Infrastructure Setup:**
- [ ] Set up PostgreSQL instance (AWS RDS or similar)
- [ ] Configure connection pooling and security
- [ ] Create development and staging PostgreSQL environments
- [ ] Set up automated backups and point-in-time recovery

**Week 2: SQLAlchemy Model Creation**
- [ ] Create SQLAlchemy models matching existing schema
- [ ] Set up Alembic for migration management
- [ ] Create initial migration from current SQLite schema
- [ ] Add proper foreign key constraints (missing in current setup)
- [ ] Implement database indexes for performance

**Week 3: Parallel Database Operations**
- [ ] Implement database abstraction layer supporting both SQLite and PostgreSQL
- [ ] Create data migration scripts with validation
- [ ] Set up dual-write system (write to both databases temporarily)
- [ ] Implement comprehensive data validation between systems

**Week 4: PostgreSQL Cutover**
- [ ] Perform full data migration during maintenance window
- [ ] Validate all data integrity checks pass
- [ ] Switch read operations to PostgreSQL
- [ ] Monitor performance and fix any query issues
- [ ] Remove SQLite dependencies after 48-hour stabilization

**Success Criteria:**
- Zero patient records lost during migration
- All existing queries work with PostgreSQL
- Performance equal or better than SQLite
- Automated migration process documented and tested

### **Month 3: Infrastructure & Monitoring**
**Objective**: Add production monitoring and improve deployment reliability

**Week 1-2: Containerization**
```dockerfile
# Multi-stage Dockerfile
FROM python:3.12-slim as builder
# Build dependencies
FROM python:3.12-slim as runtime
# Production runtime
```

**Docker Implementation:**
- [ ] Create optimized multi-stage Dockerfile
- [ ] Set up docker-compose for local development
- [ ] Configure health checks and graceful shutdown
- [ ] Implement container security best practices
- [ ] Create development environment documentation

**Week 3-4: Monitoring & Alerting**
```bash
# Add to requirements.txt
sentry-sdk[fastapi]==1.40+
prometheus-client==0.19+
structlog==23.2+
```

**Monitoring Setup:**
- [ ] Integrate Sentry for error tracking and performance monitoring
- [ ] Implement structured logging with healthcare-specific context
- [ ] Set up Prometheus metrics for business KPIs
- [ ] Create health check endpoints for all services
- [ ] Configure alerts for critical system failures
- [ ] Set up uptime monitoring and alerting

**Success Criteria:**
- Container deployment process documented and tested
- All errors automatically tracked and categorized
- Performance baselines established with alerting
- Health monitoring covers all critical system components

---

## **Phase 2: Performance & Security (Months 4-6)**
*Priority: Add caching, background processing, and enhanced security*

### **Month 4: Caching & Background Processing**
**Objective**: Improve performance and user experience with Redis and Celery

**Week 1: Redis Integration**
```bash
# Add to requirements.txt
redis==5.0+
aioredis==2.0+
celery==5.3+
flower==2.0+  # Task monitoring
```

**Redis Implementation:**
- [ ] Set up Redis cluster for session storage
- [ ] Migrate sessions from in-memory to Redis
- [ ] Implement API response caching for expensive operations
- [ ] Add cache invalidation strategies for data updates
- [ ] Configure Redis persistence and backup

**Week 2-3: Background Job System**
- [ ] Set up Celery with Redis broker
- [ ] Migrate email sending to background tasks
- [ ] Move report generation to async processing
- [ ] Implement job retry and error handling
- [ ] Add Flower monitoring dashboard
- [ ] Create job scheduling for recurring tasks (reminders, backups)

**Week 4: Performance Optimization**
- [ ] Add database query optimization and indexing
- [ ] Implement connection pooling for PostgreSQL
- [ ] Add response compression middleware
- [ ] Optimize static file serving with CDN preparation
- [ ] Implement database query monitoring

**Success Criteria:**
- API response times <200ms for 95% of requests
- Email notifications sent asynchronously
- Reports generate in background without blocking UI
- Session persistence across application restarts

### **Month 5: Enhanced Authentication & Authorization**
**Objective**: Implement JWT + RBAC + MFA for enterprise security

**Week 1: JWT Implementation**
```bash
# Add to requirements.txt
python-jose[cryptography]==3.3+
passlib[bcrypt]==1.7.4+
pyotp==2.9+  # TOTP for MFA
qrcode==7.4+  # QR code generation
```

**JWT System Setup:**
- [ ] Implement JWT token generation and validation
- [ ] Create refresh token mechanism
- [ ] Set up token blacklist in Redis
- [ ] Maintain backward compatibility with existing sessions
- [ ] Add JWT middleware with proper error handling

**Week 2: Role-Based Access Control (RBAC)**
- [ ] Define role hierarchy (Admin, Therapist, Receptionist, Read-only)
- [ ] Create permission system for granular access control
- [ ] Implement role-based endpoint protection
- [ ] Add permission checking middleware
- [ ] Create role management UI components

**Week 3: Multi-Factor Authentication**
- [ ] Implement TOTP-based 2FA with QR codes
- [ ] Add MFA setup and recovery code generation
- [ ] Create MFA verification endpoints
- [ ] Add backup authentication methods
- [ ] Implement MFA requirement policies

**Week 4: Security Hardening**
- [ ] Add comprehensive input sanitization
- [ ] Implement CORS policies for API security
- [ ] Add rate limiting per user and endpoint
- [ ] Set up security headers middleware
- [ ] Create audit logging for all authentication events

**Success Criteria:**
- JWT authentication working alongside existing sessions
- Role-based permissions enforced across all endpoints
- MFA optional but working for enhanced security accounts
- Comprehensive security audit logging in place

### **Month 6: API Enhancement & Documentation**
**Objective**: Improve API design and add comprehensive documentation

**Week 1-2: API Standardization**
- [ ] Standardize all API response formats
- [ ] Implement consistent error handling and status codes
- [ ] Add API versioning strategy
- [ ] Create comprehensive request/response models
- [ ] Add API request/response validation middleware

**Week 3-4: Documentation & Developer Experience**
- [ ] Enhanced FastAPI OpenAPI documentation with examples
- [ ] Create API integration guides
- [ ] Add Postman/Bruno collection for testing
- [ ] Set up API documentation hosting
- [ ] Create developer onboarding documentation

**Success Criteria:**
- All APIs follow consistent patterns and standards
- Complete API documentation with working examples
- External integrations possible using documented APIs
- Developer-friendly testing and integration tools

---

## **Phase 3: Frontend Modernization (Months 7-12)**
*Priority: Modern React frontend while maintaining existing functionality*

### **Month 7-8: Frontend Foundation**
**Objective**: Set up React/TypeScript foundation alongside existing templates

**Week 1-2: Next.js Setup**
```bash
# Frontend dependencies
npx create-next-app@latest hadada-frontend --typescript --tailwind --app
npm install @tanstack/react-query zustand react-hook-form @hookform/resolvers
npm install zod lucide-react @radix-ui/react-dialog @radix-ui/react-select
```

**Frontend Architecture:**
- [ ] Set up Next.js 14 with TypeScript and TailwindCSS
- [ ] Configure TanStack Query for API state management
- [ ] Set up Zustand for local state management
- [ ] Implement React Hook Form with Zod validation
- [ ] Create healthcare-specific design system components

**Week 3-4: Authentication & Navigation**
- [ ] Create login/logout components with JWT integration
- [ ] Implement protected route components
- [ ] Build navigation structure matching current app
- [ ] Add role-based component visibility
- [ ] Create responsive layout components

**Success Criteria:**
- React app runs independently with API integration
- Authentication flow working with JWT tokens
- Navigation structure matches existing application
- Design system components created for healthcare UI

### **Month 9: Patient Management Migration**
**Objective**: Migrate patient management features to React

**Week 1: Patient List & Search**
- [ ] Create patient listing component with search/filtering
- [ ] Implement pagination and sorting
- [ ] Add patient quick actions (edit, view, archive)
- [ ] Integrate with existing patient APIs
- [ ] Add loading states and error handling

**Week 2: Patient Profile & Forms**
- [ ] Build comprehensive patient profile component
- [ ] Create patient creation/editing forms
- [ ] Implement form validation matching backend rules
- [ ] Add file upload for patient documents
- [ ] Create medical history display components

**Week 3-4: Testing & Integration**
- [ ] Write component tests for patient management
- [ ] Add E2E tests for critical patient workflows
- [ ] Performance testing with large patient datasets
- [ ] Accessibility testing for healthcare compliance
- [ ] User acceptance testing with healthcare staff

**Success Criteria:**
- Patient management fully functional in React
- Performance equal or better than current implementation
- All existing patient workflows preserved
- Healthcare staff can use new interface without training

### **Month 10: Appointment & Scheduling Migration**
**Objective**: Migrate scheduling system to React with enhanced UX

**Week 1-2: Calendar Components**
- [ ] Create calendar grid components for day/week/month views
- [ ] Implement drag-and-drop appointment scheduling
- [ ] Add time slot management and availability
- [ ] Create appointment conflict detection
- [ ] Build recurring appointment components

**Week 3-4: Appointment Management**
- [ ] Create appointment creation/editing forms
- [ ] Implement appointment status management
- [ ] Add treatment note integration
- [ ] Build appointment search and filtering
- [ ] Create appointment reminder components

**Success Criteria:**
- Scheduling interface more intuitive than current system
- All appointment types and workflows supported
- Enhanced UX features (drag-drop, conflict detection)
- Integration with treatment notes maintained

### **Month 11: Treatment Notes & Clinical Features**
**Objective**: Migrate clinical documentation to React

**Week 1-2: Treatment Note Forms**
- [ ] Create treatment note entry components
- [ ] Implement SOAP note structure
- [ ] Add outcome measure integration
- [ ] Build template system for common treatments
- [ ] Create clinical decision support components

**Week 3-4: Reporting & Analytics**
- [ ] Build patient summary and progress reports
- [ ] Create treatment outcome visualizations
- [ ] Implement clinical dashboard components
- [ ] Add export functionality for reports
- [ ] Build audit trail viewing components

**Success Criteria:**
- Clinical documentation workflow improved
- Outcome measures integrated seamlessly
- Reporting capabilities enhanced with visualizations
- Audit trail accessible to authorized users

### **Month 12: Billing & Administrative Migration**
**Objective**: Complete frontend migration with billing and admin features

**Week 1-2: Billing System**
- [ ] Create billing entry and management components
- [ ] Implement invoice generation and printing
- [ ] Add payment tracking and reconciliation
- [ ] Build medical aid claim components
- [ ] Create financial reporting dashboards

**Week 3-4: Administrative Features**
- [ ] Build user management interface
- [ ] Create system settings and configuration
- [ ] Add backup and maintenance tools
- [ ] Implement audit reporting interface
- [ ] Create help and documentation system

**Success Criteria:**
- All administrative functions available in React
- Billing workflow streamlined and error-free
- System administration interface user-friendly
- Help system integrated for user support

---

## **Phase 4: Cloud Infrastructure (Months 13-15)**
*Priority: Migrate to scalable cloud infrastructure*

### **Month 13: AWS Infrastructure Setup**
**Objective**: Prepare cloud infrastructure for migration

**Week 1-2: AWS Account & Security**
- [ ] Set up AWS account with healthcare compliance settings
- [ ] Configure IAM roles and policies
- [ ] Set up AWS Secrets Manager for credentials
- [ ] Configure VPC with private/public subnets
- [ ] Set up security groups and NACLs

**Week 3-4: Core Services**
- [ ] Set up RDS PostgreSQL with Multi-AZ
- [ ] Configure ElastiCache Redis cluster
- [ ] Set up S3 buckets with encryption
- [ ] Configure CloudFront CDN
- [ ] Set up Application Load Balancer

**Success Criteria:**
- AWS infrastructure configured for healthcare compliance
- All services properly secured and monitored
- Network architecture optimized for performance
- Backup and disaster recovery procedures established

### **Month 14: Container Orchestration**
**Objective**: Set up ECS Fargate for container orchestration

**Week 1-2: ECS Setup**
- [ ] Configure ECS cluster with Fargate
- [ ] Create task definitions for all services
- [ ] Set up service discovery and load balancing
- [ ] Configure auto-scaling policies
- [ ] Implement health checks and monitoring

**Week 3-4: CI/CD Pipeline**
- [ ] Set up GitHub Actions for automated deployment
- [ ] Create build and test pipelines
- [ ] Implement blue-green deployment strategy
- [ ] Add automated rollback capabilities
- [ ] Configure deployment approvals and gates

**Success Criteria:**
- Automated deployment pipeline operational
- Blue-green deployments working reliably
- Auto-scaling responding to load appropriately
- Rollback procedures tested and documented

### **Month 15: Production Migration**
**Objective**: Complete migration to cloud infrastructure

**Week 1: Staging Validation**
- [ ] Deploy complete application to staging environment
- [ ] Perform comprehensive testing of all features
- [ ] Load testing with production-like data volumes
- [ ] Security penetration testing
- [ ] Disaster recovery testing

**Week 2: Production Cutover**
- [ ] Schedule maintenance window with users
- [ ] Migrate production data to AWS RDS
- [ ] Switch DNS to point to new infrastructure
- [ ] Monitor all systems for 48 hours
- [ ] Validate all features working correctly

**Week 3-4: Optimization**
- [ ] Optimize costs based on actual usage patterns
- [ ] Fine-tune auto-scaling and monitoring
- [ ] Update documentation and runbooks
- [ ] Train team on new infrastructure
- [ ] Plan decommissioning of old infrastructure

**Success Criteria:**
- Production running smoothly on AWS
- Performance metrics meet or exceed previous system
- All monitoring and alerting operational
- Team confident managing cloud infrastructure

---

## **Phase 5: Advanced Features (Months 16-18)**
*Priority: Add enterprise features and integrations*

### **Month 16: Healthcare Integrations**
**Objective**: Add healthcare-specific integrations and compliance features

**Week 1-2: HL7 FHIR Integration**
```bash
# Add FHIR support
pip install fhir.resources==7.0+
pip install hl7==0.4+
```

**FHIR Implementation:**
- [ ] Set up FHIR R4 server capabilities
- [ ] Create patient resource mapping
- [ ] Implement observation resources for outcome measures
- [ ] Add encounter resources for appointments
- [ ] Create diagnostic report resources

**Week 3-4: Compliance Automation**
- [ ] Implement automated POPIA compliance reporting
- [ ] Add data subject rights automation (access, deletion)
- [ ] Create audit trail export functionality
- [ ] Implement consent management system
- [ ] Add data retention policy automation

**Success Criteria:**
- FHIR resources available for external integrations
- POPIA compliance fully automated
- Audit trails comprehensive and exportable
- Data retention policies enforced automatically

### **Month 17: Advanced Analytics & AI**
**Objective**: Enhance clinical decision support and analytics

**Week 1-2: Advanced Analytics**
```bash
# Analytics dependencies
pip install pandas==2.0+ numpy==1.24+ scikit-learn==1.3+
npm install recharts d3 @visx/visx
```

**Analytics Implementation:**
- [ ] Create treatment outcome prediction models
- [ ] Build patient risk stratification algorithms
- [ ] Implement population health analytics
- [ ] Add treatment effectiveness analysis
- [ ] Create clinical quality metrics dashboard

**Week 3-4: Enhanced AI Features**
- [ ] Upgrade AI medical summary generation
- [ ] Add clinical decision support alerts
- [ ] Implement automated coding suggestions
- [ ] Create treatment plan recommendations
- [ ] Add voice-to-text for clinical notes

**Success Criteria:**
- Predictive analytics helping clinical decisions
- AI features improving documentation efficiency
- Population health insights available
- Clinical quality metrics tracked automatically

### **Month 18: Mobile & Future-Proofing**
**Objective**: Add mobile capabilities and prepare for future growth

**Week 1-2: Mobile Optimization**
- [ ] Optimize React application for mobile devices
- [ ] Create Progressive Web App (PWA) capabilities
- [ ] Add offline functionality for critical features
- [ ] Implement push notifications
- [ ] Create mobile-specific UI components

**Week 3-4: Scalability & Future Proofing**
- [ ] Implement multi-tenancy for clinic separation
- [ ] Add API rate limiting and quotas
- [ ] Create plugin architecture for future extensions
- [ ] Implement feature flags for gradual rollouts
- [ ] Add comprehensive monitoring for business metrics

**Success Criteria:**
- Mobile experience equivalent to desktop
- Multi-tenancy supporting multiple clinics
- Platform ready for future feature additions
- Comprehensive monitoring of business and technical metrics

---

## Risk Management & Mitigation

### **High-Risk Areas**

#### **Data Migration (Months 2, 13, 15)**
**Risk**: Patient data loss or corruption during database migrations
**Mitigation**:
- Multiple backup strategies before any migration
- Parallel running systems during transition periods
- Comprehensive data validation at every step
- Rollback procedures tested and documented
- Point-in-time recovery capabilities

#### **Authentication Changes (Month 5)**
**Risk**: Users locked out of system during auth migration
**Mitigation**:
- Gradual rollout with feature flags
- Maintain existing session system during transition
- Comprehensive user communication and training
- Emergency access procedures documented
- Quick rollback capability for auth components

#### **Frontend Migration (Months 7-12)**
**Risk**: User workflow disruption and resistance to change
**Mitigation**:
- Parallel development - old and new systems available
- Gradual feature migration with user choice
- Comprehensive user training and documentation
- Feedback loops for UI/UX improvements
- Rollback to old interface if needed

### **Success Metrics by Phase**

#### **Phase 1: Foundation (Months 1-3)**
- [ ] 80%+ test coverage achieved
- [ ] Zero data loss in PostgreSQL migration
- [ ] Performance maintained or improved
- [ ] Monitoring covers all critical systems

#### **Phase 2: Performance (Months 4-6)**
- [ ] API response times <200ms (95th percentile)
- [ ] Background jobs processing without blocking UI
- [ ] Authentication more secure with JWT + MFA
- [ ] API documentation complete and usable

#### **Phase 3: Frontend (Months 7-12)**
- [ ] React application feature-complete
- [ ] User satisfaction maintained or improved
- [ ] Performance equal or better than templates
- [ ] Mobile experience acceptable for healthcare use

#### **Phase 4: Cloud (Months 13-15)**
- [ ] 99.9% uptime achieved on AWS
- [ ] Auto-scaling working effectively
- [ ] Costs optimized for usage patterns
- [ ] Disaster recovery tested and functional

#### **Phase 5: Advanced (Months 16-18)**
- [ ] Healthcare integrations operational
- [ ] POPIA compliance fully automated
- [ ] AI features improving clinical workflows
- [ ] Platform ready for multi-clinic scaling

---

## Investment & Resource Planning

### **Budget Estimate**
- **Development Team**: $720,000 (18 months × $40,000/month team cost)
- **AWS Infrastructure**: $72,000 (18 months × $4,000/month growing to production scale)
- **Tools & Services**: $36,000 (monitoring, security, testing tools)
- **Training & Certification**: $18,000 (team upskilling and healthcare compliance)
- **Contingency**: $84,600 (10% buffer for unexpected challenges)
- **Total**: $930,600 over 18 months

### **Team Structure**
- **1 Senior Full-Stack Developer** (migration lead, architecture decisions)
- **1 Backend Developer** (API development, database optimization)
- **1 Frontend Developer** (React migration, UX improvements)
- **1 DevOps Engineer** (infrastructure, CI/CD, monitoring)
- **0.5 Healthcare Consultant** (compliance, workflow optimization)
- **0.5 QA Engineer** (testing, quality assurance)

### **ROI Justification**
- **Scalability**: Platform capable of supporting 10x current user base
- **Efficiency**: 40% improvement in development velocity after migration
- **Reliability**: 99.9% uptime vs current occasional downtime
- **Compliance**: Automated compliance reducing audit costs
- **Market Position**: Enterprise-ready platform for larger contracts

---

## Communication & Change Management

### **Stakeholder Communication Plan**

#### **Healthcare Staff (Primary Users)**
- **Month 1**: Migration announcement and timeline
- **Monthly**: Progress updates and feature previews
- **Months 7-12**: Gradual introduction to new frontend
- **Training sessions**: Before each major interface change

#### **Management & Investors**
- **Quarterly reviews**: Progress, budget, and ROI metrics
- **Risk assessments**: Monthly risk and mitigation updates
- **Business impact**: Continuous monitoring of user satisfaction

#### **Development Team**
- **Weekly standups**: Progress tracking and blocker removal
- **Monthly retrospectives**: Process improvements and lessons learned
- **Quarterly planning**: Adjustments to timeline and priorities

### **Change Management Strategy**

#### **User Adoption**
- Gradual introduction of new features with opt-in capability
- Comprehensive training materials and video tutorials
- On-site support during critical migration phases
- Feedback collection and rapid response to user concerns

#### **Technical Team Transition**
- Documentation of all architectural decisions
- Knowledge transfer sessions for new technologies
- Pair programming during critical migration phases
- Post-migration support and optimization period

---

## Conclusion

This migration roadmap transforms HadadaHealth from a functional healthcare application to an enterprise-ready platform capable of serving hundreds of clinics. The 18-month timeline balances aggressive feature development with risk management and user experience preservation.

**Key Success Factors:**
1. **Safety First**: Comprehensive testing and backup strategies protect patient data
2. **Incremental Change**: Gradual migration reduces risk and user disruption
3. **Continuous Value**: Each phase delivers immediate benefits while building toward the final vision
4. **Healthcare Focus**: All decisions prioritize patient care and regulatory compliance

The investment of $930,600 over 18 months positions the platform for significant growth and establishes a technological foundation that can scale with business success.

---

*This roadmap should be reviewed monthly and adjusted based on progress, user feedback, and changing business requirements.*