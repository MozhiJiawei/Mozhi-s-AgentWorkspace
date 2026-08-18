from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
DEPLOY = ROOT / "deploy" / "resource-server"


class DeploymentLayoutTests(unittest.TestCase):
    def test_required_deployment_files_exist(self):
        required = [
            "compose.production.yml",
            "compose.local.yml",
            "edge/Dockerfile",
            "edge/Dockerfile.source",
            "edge/entrypoint.sh",
            "edge/Caddyfile.template",
            "docs/Dockerfile",
            "docs/entrypoint.sh",
            "docs/nginx.conf",
            "ccn-api/Dockerfile",
            "scripts/release.py",
            "scripts/install.sh",
            "scripts/rollback.sh",
            "scripts/backup-ccn.sh",
            "scripts/restore-ccn.sh",
            "scripts/smoke-test.py",
            "scripts/update-ccn-source.sh",
            "scripts/update-edge-source.sh",
        ]
        self.assertEqual([], [path for path in required if not (DEPLOY / path).is_file()])

    def test_production_compose_does_not_publish_internal_ports(self):
        compose = (DEPLOY / "compose.production.yml").read_text(encoding="utf-8")
        self.assertNotIn('"5432:5432"', compose)
        self.assertNotIn('"6379:6379"', compose)
        self.assertNotIn('"8000:8000"', compose)
        for public_port in ('"80:80"', '"443:443"', '"7000:7000"', '"8888:8888"'):
            self.assertIn(public_port, compose)
        self.assertIn("name: mozhi-agent-services-edge\n    external: true", compose)

    def test_install_supports_verified_preloaded_images(self):
        install = (DEPLOY / "scripts" / "install.sh").read_text(encoding="utf-8")
        self.assertIn("SKIP_IMAGE_BUILD", install)
        self.assertIn("docker image inspect", install)

    def test_ccn_source_updates_do_not_build_or_recreate_after_bootstrap(self):
        compose = (DEPLOY / "compose.production.yml").read_text(encoding="utf-8")
        updater = (DEPLOY / "scripts/update-ccn-source.sh").read_text(encoding="utf-8")
        release = (DEPLOY / "scripts/release.py").read_text(encoding="utf-8")
        self.assertIn("../../loops/ccn-brief-report/task_service:/app:ro", compose)
        self.assertIn('docker start "$CONTAINER"', updater)
        self.assertIn("--no-build --force-recreate", updater)
        self.assertIn('if [ -z "$mounted_source" ]', updater)
        self.assertIn('sub.add_parser("deploy-ccn-source")', release)
        self.assertIn("sha256sum", release)
        self.assertIn('cmp -s "$INCOMING/pyproject.toml"', updater)
        self.assertIn('"$INCOMING/migrations" "$TARGET/migrations"', updater)
        self.assertNotIn('cp -a "$TARGET/." "$backup/" 2>/dev/null || true', updater)
        self.assertIn("trap finish EXIT", updater)

    def test_full_install_sets_rollback_before_switching_deploy_directory(self):
        install = (DEPLOY / "scripts/install.sh").read_text(encoding="utf-8")
        self.assertLess(install.index("trap finish_install EXIT"), install.index('mv "$DEPLOY_PATH" "$PREVIOUS_PATH"'))
        self.assertIn("trap 'exit 130' INT TERM", install)
        self.assertIn("trap - EXIT INT TERM", install)

    def test_release_passes_custom_deploy_path_to_rollback(self):
        release = (DEPLOY / "scripts/release.py").read_text(encoding="utf-8")
        self.assertIn('DEPLOY_PATH={sh_quote(args.deploy_path)} COMPONENT=', release)

    def test_inferenceviz_route_uses_shared_edge_network_upstream(self):
        template = (DEPLOY / "edge/Caddyfile.template").read_text(encoding="utf-8")
        entrypoint = (DEPLOY / "edge/entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn("https://${INFERENCEVIZ_DOMAIN}", template)
        self.assertIn("reverse_proxy ${INFERENCEVIZ_UPSTREAM}", template)
        self.assertIn("inferenceviz.haohaoxiaoyu.top", entrypoint)
        self.assertIn("inferenceviz-web:8080", entrypoint)

    def test_edge_source_release_is_scoped_and_rolls_back(self):
        release = (DEPLOY / "scripts/release.py").read_text(encoding="utf-8")
        updater = (DEPLOY / "scripts/update-edge-source.sh").read_text(encoding="utf-8")
        self.assertIn('sub.add_parser("deploy-edge-source")', release)
        self.assertIn("ensure_paths_clean(EDGE_SOURCE_FILES)", release)
        self.assertIn("sha256sum", release)
        self.assertIn("mozhi-agent-service-edge:previous", updater)
        self.assertIn("Dockerfile.source", updater)
        self.assertNotIn('docker compose -f "$COMPOSE" build edge', updater)
        self.assertIn("https://ccn-api.haohaoxiaoyu.top/healthz", updater)
        self.assertIn("restore", updater)
        self.assertNotIn("docker compose down", updater)

    def test_legacy_client_files_remain_outside_service(self):
        loop = ROOT / "loops" / "ccn-brief-report"
        for name in ("task_api.py", "config.json", "local_state.py", "LOOP.md", "policy.md"):
            self.assertTrue((loop / name).is_file())

    def test_old_deployment_entrypoints_were_removed(self):
        old_paths = [
            "Dockerfile",
            "compose.docs.yml",
            "deploy/deploy-docs.sh",
            "docker/entrypoint.sh",
            "docker/nginx.conf",
            "scripts/docs_compose.ps1",
            "scripts/release_docs_package.py",
        ]
        self.assertEqual([], [path for path in old_paths if (ROOT / path).exists()])


if __name__ == "__main__":
    unittest.main()
