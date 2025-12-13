-- Project Alpha Seed Data
-- 执行此文件前请确保已运行数据库迁移（alembic upgrade head）
--
-- 执行方式（推荐）：
--   psql -U postgres -d projectalpha -f seed.sql
--
-- 如果遇到编码错误，可以尝试：
--   1. 确保文件以 UTF-8 编码保存
--   2. 使用环境变量设置编码：PGCLIENTENCODING=UTF8 psql -U postgres -d projectalpha -f seed.sql
--   3. 或者在 psql 中先执行：SET client_encoding = 'UTF8';
--
-- 注意：确保数据库名称正确（默认可能是 postgres，不是 projectalpha）

-- 设置客户端编码为 UTF-8（解决中文编码问题）
SET client_encoding = 'UTF8';

-- 清理现有数据（可选，谨慎使用）
-- TRUNCATE TABLE ticket_tags CASCADE;
-- TRUNCATE TABLE tickets CASCADE;
-- TRUNCATE TABLE tags CASCADE;

-- ============================================
-- 插入 Tags
-- ============================================

-- Platform Tags
INSERT INTO tags (id, name, created_at) VALUES
(gen_random_uuid(), 'ios', now()),
(gen_random_uuid(), 'android', now()),
(gen_random_uuid(), 'web', now()),
(gen_random_uuid(), 'windows', now()),
(gen_random_uuid(), 'macos', now()),
(gen_random_uuid(), 'linux', now());

-- Project Tags
INSERT INTO tags (id, name, created_at) VALUES
(gen_random_uuid(), 'viking', now()),
(gen_random_uuid(), 'atlas', now()),
(gen_random_uuid(), 'phoenix', now()),
(gen_random_uuid(), 'nexus', now()),
(gen_random_uuid(), 'quantum', now());

-- Functional Tags
INSERT INTO tags (id, name, created_at) VALUES
(gen_random_uuid(), 'autocomplete', now()),
(gen_random_uuid(), 'search', now()),
(gen_random_uuid(), 'authentication', now()),
(gen_random_uuid(), 'authorization', now()),
(gen_random_uuid(), 'payment', now()),
(gen_random_uuid(), 'notification', now()),
(gen_random_uuid(), 'analytics', now()),
(gen_random_uuid(), 'logging', now()),
(gen_random_uuid(), 'caching', now()),
(gen_random_uuid(), 'api', now()),
(gen_random_uuid(), 'database', now()),
(gen_random_uuid(), 'ui', now()),
(gen_random_uuid(), 'ux', now()),
(gen_random_uuid(), 'performance', now()),
(gen_random_uuid(), 'security', now()),
(gen_random_uuid(), 'testing', now()),
(gen_random_uuid(), 'deployment', now()),
(gen_random_uuid(), 'monitoring', now()),
(gen_random_uuid(), 'documentation', now());

-- Priority Tags
INSERT INTO tags (id, name, created_at) VALUES
(gen_random_uuid(), 'urgent', now()),
(gen_random_uuid(), 'high', now()),
(gen_random_uuid(), 'medium', now()),
(gen_random_uuid(), 'low', now()),
(gen_random_uuid(), 'bug', now()),
(gen_random_uuid(), 'feature', now()),
(gen_random_uuid(), 'enhancement', now()),
(gen_random_uuid(), 'refactor', now());

-- Component Tags
INSERT INTO tags (id, name, created_at) VALUES
(gen_random_uuid(), 'frontend', now()),
(gen_random_uuid(), 'backend', now()),
(gen_random_uuid(), 'mobile', now()),
(gen_random_uuid(), 'desktop', now()),
(gen_random_uuid(), 'server', now()),
(gen_random_uuid(), 'client', now());

-- ============================================
-- 插入 Tickets (50个)
-- ============================================

-- 1-10: Viking 项目相关
INSERT INTO tickets (id, title, description, status, created_at, updated_at) VALUES
(gen_random_uuid(), '实现 Viking 项目的用户认证系统', '需要支持 OAuth2 和 JWT token，包括登录、注册、密码重置功能', 'open', now() - interval '30 days', now() - interval '25 days'),
(gen_random_uuid(), 'Viking iOS 应用首页 UI 优化', '重新设计首页布局，提升用户体验和视觉效果', 'open', now() - interval '28 days', now() - interval '20 days'),
(gen_random_uuid(), 'Viking 项目支付模块集成', '集成 Stripe 支付网关，支持多种支付方式', 'done', now() - interval '25 days', now() - interval '15 days'),
(gen_random_uuid(), 'Viking Android 应用性能优化', '优化应用启动速度和内存使用，减少卡顿现象', 'open', now() - interval '22 days', now() - interval '18 days'),
(gen_random_uuid(), 'Viking 项目搜索功能增强', '实现全文搜索和智能推荐功能', 'open', now() - interval '20 days', now() - interval '10 days'),
(gen_random_uuid(), 'Viking 后端 API 限流机制', '实现基于 Redis 的 API 限流，防止恶意请求', 'done', now() - interval '18 days', now() - interval '12 days'),
(gen_random_uuid(), 'Viking 项目通知系统重构', '重构推送通知系统，支持多渠道推送', 'open', now() - interval '15 days', now() - interval '8 days'),
(gen_random_uuid(), 'Viking Web 端响应式设计', '优化移动端和桌面端的响应式布局', 'open', now() - interval '12 days', now() - interval '5 days'),
(gen_random_uuid(), 'Viking 数据分析仪表板', '创建实时数据分析和可视化仪表板', 'done', now() - interval '10 days', now() - interval '3 days'),
(gen_random_uuid(), 'Viking 项目文档完善', '补充 API 文档和开发指南', 'open', now() - interval '8 days', now() - interval '2 days');

-- 11-20: Atlas 项目相关
INSERT INTO tickets (id, title, description, status, created_at, updated_at) VALUES
(gen_random_uuid(), 'Atlas 项目数据库迁移脚本', '编写从旧版本到新版本的数据库迁移脚本', 'open', now() - interval '27 days', now() - interval '22 days'),
(gen_random_uuid(), 'Atlas macOS 应用菜单栏功能', '实现菜单栏快捷操作和状态显示', 'done', now() - interval '24 days', now() - interval '16 days'),
(gen_random_uuid(), 'Atlas 项目缓存策略优化', '优化 Redis 缓存策略，提升查询性能', 'open', now() - interval '21 days', now() - interval '14 days'),
(gen_random_uuid(), 'Atlas Linux 服务器部署脚本', '编写自动化部署脚本，支持 Docker 容器化', 'open', now() - interval '19 days', now() - interval '11 days'),
(gen_random_uuid(), 'Atlas 项目安全审计', '进行安全漏洞扫描和代码审计', 'open', now() - interval '17 days', now() - interval '9 days'),
(gen_random_uuid(), 'Atlas Web 端自动完成功能', '实现智能输入自动完成，提升用户体验', 'done', now() - interval '14 days', now() - interval '7 days'),
(gen_random_uuid(), 'Atlas 项目日志系统升级', '升级日志系统，支持结构化日志和日志聚合', 'open', now() - interval '11 days', now() - interval '4 days'),
(gen_random_uuid(), 'Atlas Windows 应用安装程序', '创建 Windows 安装包和自动更新机制', 'open', now() - interval '9 days', now() - interval '1 days'),
(gen_random_uuid(), 'Atlas 项目单元测试覆盖率提升', '将单元测试覆盖率提升至 80% 以上', 'done', now() - interval '6 days', now() - interval '2 days'),
(gen_random_uuid(), 'Atlas 项目监控告警配置', '配置 Prometheus 和 Grafana 监控告警', 'open', now() - interval '4 days', now());

-- 21-30: Phoenix 项目相关
INSERT INTO tickets (id, title, description, status, created_at, updated_at) VALUES
(gen_random_uuid(), 'Phoenix 项目用户权限系统', '实现基于角色的访问控制（RBAC）', 'open', now() - interval '26 days', now() - interval '19 days'),
(gen_random_uuid(), 'Phoenix iOS 应用深色模式支持', '添加深色模式主题切换功能', 'done', now() - interval '23 days', now() - interval '17 days'),
(gen_random_uuid(), 'Phoenix 项目 API 版本管理', '实现 API 版本控制和向后兼容机制', 'open', now() - interval '20 days', now() - interval '13 days'),
(gen_random_uuid(), 'Phoenix Android 应用离线功能', '实现离线数据同步和缓存机制', 'open', now() - interval '18 days', now() - interval '10 days'),
(gen_random_uuid(), 'Phoenix 项目数据库查询优化', '优化慢查询，添加必要的数据库索引', 'open', now() - interval '16 days', now() - interval '8 days'),
(gen_random_uuid(), 'Phoenix Web 端组件库重构', '重构 UI 组件库，提升代码复用性', 'done', now() - interval '13 days', now() - interval '6 days'),
(gen_random_uuid(), 'Phoenix 项目 CI/CD 流程优化', '优化持续集成和部署流程，缩短构建时间', 'open', now() - interval '10 days', now() - interval '3 days'),
(gen_random_uuid(), 'Phoenix macOS 应用快捷键支持', '添加全局快捷键和自定义快捷键功能', 'open', now() - interval '7 days', now() - interval '1 days'),
(gen_random_uuid(), 'Phoenix 项目错误追踪系统', '集成 Sentry 错误追踪和性能监控', 'done', now() - interval '5 days', now() - interval '2 days'),
(gen_random_uuid(), 'Phoenix Linux 服务器性能调优', '优化服务器配置和资源使用', 'open', now() - interval '3 days', now());

-- 31-40: Nexus 和 Quantum 项目相关
INSERT INTO tickets (id, title, description, status, created_at, updated_at) VALUES
(gen_random_uuid(), 'Nexus 项目多语言支持', '实现国际化（i18n）和多语言切换', 'open', now() - interval '29 days', now() - interval '24 days'),
(gen_random_uuid(), 'Nexus iOS 应用推送通知', '实现本地和远程推送通知功能', 'done', now() - interval '26 days', now() - interval '18 days'),
(gen_random_uuid(), 'Nexus 项目微服务架构重构', '将单体应用拆分为微服务架构', 'open', now() - interval '24 days', now() - interval '15 days'),
(gen_random_uuid(), 'Nexus Android 应用 Material Design', '遵循 Material Design 设计规范', 'open', now() - interval '22 days', now() - interval '12 days'),
(gen_random_uuid(), 'Nexus 项目数据备份策略', '实现自动化数据备份和恢复机制', 'open', now() - interval '19 days', now() - interval '7 days'),
(gen_random_uuid(), 'Quantum 项目实时通信功能', '实现 WebSocket 实时通信和消息推送', 'done', now() - interval '16 days', now() - interval '9 days'),
(gen_random_uuid(), 'Quantum Web 端 PWA 支持', '将 Web 应用改造为 Progressive Web App', 'open', now() - interval '13 days', now() - interval '5 days'),
(gen_random_uuid(), 'Quantum 项目负载均衡配置', '配置 Nginx 负载均衡和健康检查', 'open', now() - interval '10 days', now() - interval '2 days'),
(gen_random_uuid(), 'Quantum Windows 应用系统托盘', '实现系统托盘图标和通知功能', 'done', now() - interval '7 days', now() - interval '3 days'),
(gen_random_uuid(), 'Quantum 项目 API 文档生成', '使用 Swagger/OpenAPI 自动生成 API 文档', 'open', now() - interval '5 days', now());

-- 41-50: 通用功能和 Bug 修复
INSERT INTO tickets (id, title, description, status, created_at, updated_at) VALUES
(gen_random_uuid(), '修复用户登录时偶尔出现的 500 错误', '排查并修复登录接口的异常处理问题', 'done', now() - interval '25 days', now() - interval '20 days'),
(gen_random_uuid(), '优化搜索功能的响应时间', '将搜索响应时间从 2 秒降低到 500 毫秒以内', 'open', now() - interval '23 days', now() - interval '16 days'),
(gen_random_uuid(), '修复移动端页面滚动卡顿问题', '优化 CSS 动画和 JavaScript 性能', 'done', now() - interval '21 days', now() - interval '14 days'),
(gen_random_uuid(), '增强密码强度验证规则', '添加更严格的密码复杂度要求', 'open', now() - interval '19 days', now() - interval '11 days'),
(gen_random_uuid(), '修复文件上传大小限制问题', '调整文件上传大小限制和错误提示', 'open', now() - interval '17 days', now() - interval '9 days'),
(gen_random_uuid(), '优化数据库连接池配置', '调整连接池大小和超时设置，提升性能', 'done', now() - interval '15 days', now() - interval '8 days'),
(gen_random_uuid(), '修复时区显示不正确的问题', '统一时区处理逻辑，确保时间显示准确', 'open', now() - interval '12 days', now() - interval '4 days'),
(gen_random_uuid(), '增强表单验证错误提示', '改进表单验证错误信息的显示方式', 'open', now() - interval '9 days', now() - interval '1 days'),
(gen_random_uuid(), '修复内存泄漏问题', '排查并修复长时间运行后的内存泄漏', 'done', now() - interval '6 days', now() - interval '2 days'),
(gen_random_uuid(), '优化图片加载性能', '实现图片懒加载和 WebP 格式支持', 'open', now() - interval '3 days', now());

-- ============================================
-- 关联 Tickets 和 Tags
-- ============================================

-- 使用 DO 块来关联 tickets 和 tags
DO $$
DECLARE
    tag_ios_id UUID;
    tag_android_id UUID;
    tag_web_id UUID;
    tag_windows_id UUID;
    tag_macos_id UUID;
    tag_linux_id UUID;
    tag_viking_id UUID;
    tag_atlas_id UUID;
    tag_phoenix_id UUID;
    tag_nexus_id UUID;
    tag_quantum_id UUID;
    tag_autocomplete_id UUID;
    tag_search_id UUID;
    tag_auth_id UUID;
    tag_payment_id UUID;
    tag_notification_id UUID;
    tag_analytics_id UUID;
    tag_performance_id UUID;
    tag_security_id UUID;
    tag_bug_id UUID;
    tag_feature_id UUID;
    tag_urgent_id UUID;
    tag_high_id UUID;
    tag_medium_id UUID;
    tag_low_id UUID;
    tag_frontend_id UUID;
    tag_backend_id UUID;
    tag_mobile_id UUID;
    tag_ui_id UUID;
    tag_ux_id UUID;
    tag_documentation_id UUID;
    ticket_rec RECORD;
    ticket_counter INT := 0;
BEGIN
    -- 获取所有 tag IDs
    SELECT id INTO tag_ios_id FROM tags WHERE name = 'ios';
    SELECT id INTO tag_android_id FROM tags WHERE name = 'android';
    SELECT id INTO tag_web_id FROM tags WHERE name = 'web';
    SELECT id INTO tag_windows_id FROM tags WHERE name = 'windows';
    SELECT id INTO tag_macos_id FROM tags WHERE name = 'macos';
    SELECT id INTO tag_linux_id FROM tags WHERE name = 'linux';
    SELECT id INTO tag_viking_id FROM tags WHERE name = 'viking';
    SELECT id INTO tag_atlas_id FROM tags WHERE name = 'atlas';
    SELECT id INTO tag_phoenix_id FROM tags WHERE name = 'phoenix';
    SELECT id INTO tag_nexus_id FROM tags WHERE name = 'nexus';
    SELECT id INTO tag_quantum_id FROM tags WHERE name = 'quantum';
    SELECT id INTO tag_autocomplete_id FROM tags WHERE name = 'autocomplete';
    SELECT id INTO tag_search_id FROM tags WHERE name = 'search';
    SELECT id INTO tag_auth_id FROM tags WHERE name = 'authentication';
    SELECT id INTO tag_payment_id FROM tags WHERE name = 'payment';
    SELECT id INTO tag_notification_id FROM tags WHERE name = 'notification';
    SELECT id INTO tag_analytics_id FROM tags WHERE name = 'analytics';
    SELECT id INTO tag_performance_id FROM tags WHERE name = 'performance';
    SELECT id INTO tag_security_id FROM tags WHERE name = 'security';
    SELECT id INTO tag_bug_id FROM tags WHERE name = 'bug';
    SELECT id INTO tag_feature_id FROM tags WHERE name = 'feature';
    SELECT id INTO tag_urgent_id FROM tags WHERE name = 'urgent';
    SELECT id INTO tag_high_id FROM tags WHERE name = 'high';
    SELECT id INTO tag_medium_id FROM tags WHERE name = 'medium';
    SELECT id INTO tag_low_id FROM tags WHERE name = 'low';
    SELECT id INTO tag_frontend_id FROM tags WHERE name = 'frontend';
    SELECT id INTO tag_backend_id FROM tags WHERE name = 'backend';
    SELECT id INTO tag_mobile_id FROM tags WHERE name = 'mobile';
    SELECT id INTO tag_ui_id FROM tags WHERE name = 'ui';
    SELECT id INTO tag_ux_id FROM tags WHERE name = 'ux';
    SELECT id INTO tag_documentation_id FROM tags WHERE name = 'documentation';

    -- 为每个 ticket 关联相应的 tags
    FOR ticket_rec IN SELECT id, title FROM tickets ORDER BY created_at
    LOOP
        ticket_counter := ticket_counter + 1;

        -- Ticket 1: Viking 认证系统
        IF ticket_counter = 1 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_auth_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 2: Viking iOS UI
        IF ticket_counter = 2 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ios_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ui_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ux_id);
        END IF;

        -- Ticket 3: Viking 支付
        IF ticket_counter = 3 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_payment_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 4: Viking Android 性能
        IF ticket_counter = 4 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_android_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_mobile_id);
        END IF;

        -- Ticket 5: Viking 搜索
        IF ticket_counter = 5 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_search_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_autocomplete_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 6: Viking API 限流
        IF ticket_counter = 6 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_security_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 7: Viking 通知
        IF ticket_counter = 7 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_notification_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 8: Viking Web 响应式
        IF ticket_counter = 8 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_web_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ui_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ux_id);
        END IF;

        -- Ticket 9: Viking 分析
        IF ticket_counter = 9 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_analytics_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 10: Viking 文档
        IF ticket_counter = 10 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_viking_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_documentation_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_low_id);
        END IF;

        -- Ticket 11: Atlas 数据库迁移
        IF ticket_counter = 11 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 12: Atlas macOS
        IF ticket_counter = 12 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_macos_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 13: Atlas 缓存
        IF ticket_counter = 13 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
        END IF;

        -- Ticket 14: Atlas Linux 部署
        IF ticket_counter = 14 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_linux_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 15: Atlas 安全审计
        IF ticket_counter = 15 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_security_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 16: Atlas 自动完成
        IF ticket_counter = 16 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_web_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_autocomplete_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 17: Atlas 日志
        IF ticket_counter = 17 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 18: Atlas Windows
        IF ticket_counter = 18 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_windows_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 19: Atlas 测试
        IF ticket_counter = 19 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 20: Atlas 监控
        IF ticket_counter = 20 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_atlas_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 21: Phoenix 权限
        IF ticket_counter = 21 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_auth_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_security_id);
        END IF;

        -- Ticket 22: Phoenix iOS 深色模式
        IF ticket_counter = 22 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ios_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ui_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 23: Phoenix API 版本
        IF ticket_counter = 23 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 24: Phoenix Android 离线
        IF ticket_counter = 24 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_android_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_mobile_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 25: Phoenix 数据库优化
        IF ticket_counter = 25 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
        END IF;

        -- Ticket 26: Phoenix UI 组件
        IF ticket_counter = 26 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_frontend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ui_id);
        END IF;

        -- Ticket 27: Phoenix CI/CD
        IF ticket_counter = 27 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 28: Phoenix macOS 快捷键
        IF ticket_counter = 28 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_macos_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 29: Phoenix 错误追踪
        IF ticket_counter = 29 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
        END IF;

        -- Ticket 30: Phoenix Linux 性能
        IF ticket_counter = 30 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_phoenix_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_linux_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
        END IF;

        -- Ticket 31: Nexus i18n
        IF ticket_counter = 31 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_nexus_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_frontend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 32: Nexus iOS 推送
        IF ticket_counter = 32 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_nexus_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ios_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_notification_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_mobile_id);
        END IF;

        -- Ticket 33: Nexus 微服务
        IF ticket_counter = 33 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_nexus_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 34: Nexus Android Material
        IF ticket_counter = 34 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_nexus_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_android_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ui_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ux_id);
        END IF;

        -- Ticket 35: Nexus 备份
        IF ticket_counter = 35 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_nexus_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_security_id);
        END IF;

        -- Ticket 36: Quantum WebSocket
        IF ticket_counter = 36 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_quantum_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 37: Quantum PWA
        IF ticket_counter = 37 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_quantum_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_web_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_frontend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 38: Quantum 负载均衡
        IF ticket_counter = 38 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_quantum_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
        END IF;

        -- Ticket 39: Quantum Windows 托盘
        IF ticket_counter = 39 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_quantum_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_windows_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_feature_id);
        END IF;

        -- Ticket 40: Quantum API 文档
        IF ticket_counter = 40 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_quantum_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_low_id);
        END IF;

        -- Ticket 41: Bug 修复 - 登录错误
        IF ticket_counter = 41 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_bug_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_urgent_id);
        END IF;

        -- Ticket 42: 搜索性能优化
        IF ticket_counter = 42 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_search_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 43: Bug 修复 - 移动端卡顿
        IF ticket_counter = 43 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_bug_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_mobile_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 44: 密码验证增强
        IF ticket_counter = 44 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_security_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_medium_id);
        END IF;

        -- Ticket 45: Bug 修复 - 文件上传
        IF ticket_counter = 45 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_bug_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_medium_id);
        END IF;

        -- Ticket 46: 数据库连接池优化
        IF ticket_counter = 46 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_medium_id);
        END IF;

        -- Ticket 47: Bug 修复 - 时区
        IF ticket_counter = 47 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_bug_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_medium_id);
        END IF;

        -- Ticket 48: 表单验证改进
        IF ticket_counter = 48 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_frontend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_ux_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_medium_id);
        END IF;

        -- Ticket 49: Bug 修复 - 内存泄漏
        IF ticket_counter = 49 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_bug_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_backend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_high_id);
        END IF;

        -- Ticket 50: 图片加载优化
        IF ticket_counter = 50 THEN
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_frontend_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_performance_id);
            INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (ticket_rec.id, tag_medium_id);
        END IF;

    END LOOP;
END $$;

-- 验证数据
SELECT 'Tags count:' as info, COUNT(*) as count FROM tags
UNION ALL
SELECT 'Tickets count:', COUNT(*) FROM tickets
UNION ALL
SELECT 'Ticket-Tag relations:', COUNT(*) FROM ticket_tags;
