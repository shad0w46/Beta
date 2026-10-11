"""APT backend wrapper for fast querying and package operations."""

import os
import subprocess
from typing import Dict, List, Optional, Any


class AptPackageInfo:
    def __init__(self, name: str, installed: bool = False, version: str = "",
                 candidate_version: str = "", summary: str = "",
                 description: str = "", section: str = "", size_bytes: int = 0,
                 is_upgradable: bool = False):
        self.name = name
        self.is_installed = installed
        self.version = version
        self.candidate_version = candidate_version
        self.summary = summary
        self.description = description
        self.section = section
        self.size_bytes = size_bytes
        self.is_upgradable = is_upgradable

    @property
    def display_size(self) -> str:
        if self.size_bytes <= 0:
            return "N/A"
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"


class AptBackend:
    """Manages package search, inspection, and command preparation."""

    def __init__(self):
        self._apt_available = False
        try:
            import apt
            self._apt_available = True
        except ImportError:
            self._apt_available = False

    def search_packages(self, query: str, limit: int = 80) -> List[AptPackageInfo]:
        """Search APT packages matching query in name or summary."""
        query_lower = query.strip().lower()
        results: List[AptPackageInfo] = []

        if self._apt_available:
            try:
                import apt
                cache = apt.Cache()
                # Fast name match first
                for pkg_name in cache.keys():
                    if query_lower in pkg_name.lower():
                        pkg = cache[pkg_name]
                        installed = pkg.is_installed
                        curr_ver = pkg.installed.version if installed and pkg.installed else ""
                        cand_ver = pkg.candidate.version if pkg.candidate else ""
                        summary = pkg.candidate.summary if pkg.candidate and pkg.candidate.summary else ""
                        section = pkg.candidate.section if pkg.candidate and pkg.candidate.section else ""
                        size = pkg.candidate.size if pkg.candidate else 0
                        upgradable = pkg.is_upgradable

                        results.append(AptPackageInfo(
                            name=pkg_name,
                            installed=installed,
                            version=curr_ver,
                            candidate_version=cand_ver,
                            summary=summary,
                            section=section,
                            size_bytes=size,
                            is_upgradable=upgradable
                        ))
                        if len(results) >= limit:
                            break
                return results
            except Exception:
                pass

        # Fallback to apt-cache search
        try:
            cmd = ["apt-cache", "search", query_lower]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().splitlines()
            for line in lines[:limit]:
                if " - " in line:
                    pkg_name, summary = line.split(" - ", 1)
                    results.append(AptPackageInfo(
                        name=pkg_name.strip(),
                        summary=summary.strip()
                    ))
        except Exception:
            pass

        return results

    def get_upgradable_packages(self) -> List[AptPackageInfo]:
        """Fetch list of all upgradable packages."""
        results: List[AptPackageInfo] = []
        if self._apt_available:
            try:
                import apt
                cache = apt.Cache()
                for pkg in cache:
                    if pkg.is_upgradable:
                        curr_ver = pkg.installed.version if pkg.installed else ""
                        cand_ver = pkg.candidate.version if pkg.candidate else ""
                        summary = pkg.candidate.summary if pkg.candidate and pkg.candidate.summary else ""
                        results.append(AptPackageInfo(
                            name=pkg.name,
                            installed=True,
                            version=curr_ver,
                            candidate_version=cand_ver,
                            summary=summary,
                            is_upgradable=True
                        ))
                return results
            except Exception:
                pass

        try:
            res = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines():
                if "/" in line:
                    parts = line.split()
                    pkg_name = parts[0].split("/")[0]
                    cand_ver = parts[1] if len(parts) > 1 else ""
                    results.append(AptPackageInfo(
                        name=pkg_name,
                        installed=True,
                        candidate_version=cand_ver,
                        is_upgradable=True
                    ))
        except Exception:
            pass

        return results

    def get_installed_packages(self, limit: int = 150) -> List[AptPackageInfo]:
        """Fetch installed packages."""
        results: List[AptPackageInfo] = []
        if self._apt_available:
            try:
                import apt
                cache = apt.Cache()
                for pkg in cache:
                    if pkg.is_installed:
                        curr_ver = pkg.installed.version if pkg.installed else ""
                        cand_ver = pkg.candidate.version if pkg.candidate else ""
                        summary = pkg.candidate.summary if pkg.candidate and pkg.candidate.summary else ""
                        results.append(AptPackageInfo(
                            name=pkg.name,
                            installed=True,
                            version=curr_ver,
                            candidate_version=cand_ver,
                            summary=summary,
                            is_upgradable=pkg.is_upgradable
                        ))
                        if len(results) >= limit:
                            break
                return results
            except Exception:
                pass

        try:
            res = subprocess.run(["dpkg-query", "-W", "-f=${Package}\\t${Version}\\t${Status}\\n"],
                                 capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines()[:limit]:
                parts = line.split("\t")
                if len(parts) >= 3 and "installed" in parts[2]:
                    results.append(AptPackageInfo(
                        name=parts[0],
                        installed=True,
                        version=parts[1]
                    ))
        except Exception:
            pass

        return results

    def get_package_detail(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get complete package details (dependencies, description, maintainer)."""
        if self._apt_available:
            try:
                import apt
                cache = apt.Cache()
                if package_name in cache:
                    pkg = cache[package_name]
                    version_obj = pkg.installed if pkg.is_installed else pkg.candidate
                    if not version_obj and pkg.candidate:
                        version_obj = pkg.candidate

                    deps = []
                    if version_obj and hasattr(version_obj, "dependencies"):
                        for dep_or in version_obj.dependencies:
                            deps.append(", ".join([d.name for d in dep_or]))

                    return {
                        "name": pkg.name,
                        "installed": pkg.is_installed,
                        "version": pkg.installed.version if pkg.is_installed and pkg.installed else "None",
                        "candidate": pkg.candidate.version if pkg.candidate else "None",
                        "summary": version_obj.summary if version_obj else "",
                        "description": version_obj.description if version_obj else "",
                        "section": version_obj.section if version_obj else "",
                        "size": version_obj.size if version_obj else 0,
                        "installed_size": version_obj.installed_size if version_obj else 0,
                        "homepage": getattr(version_obj, "homepage", ""),
                        "dependencies": deps[:15],
                        "upgradable": pkg.is_upgradable
                    }
            except Exception:
                pass

        # Fallback to apt-cache show
        try:
            res = subprocess.run(["apt-cache", "show", package_name], capture_output=True, text=True, timeout=4)
            data = {"name": package_name, "installed": False, "dependencies": []}
            for line in res.stdout.splitlines():
                if line.startswith("Version: "):
                    data["candidate"] = line.replace("Version: ", "").strip()
                elif line.startswith("Section: "):
                    data["section"] = line.replace("Section: ", "").strip()
                elif line.startswith("Description: "):
                    data["summary"] = line.replace("Description: ", "").strip()
                elif line.startswith("Homepage: "):
                    data["homepage"] = line.replace("Homepage: ", "").strip()
            return data
        except Exception:
            return None

    # CLI Command Generators for Runner
    @staticmethod
    def cmd_update() -> List[str]:
        return ["apt-get", "update"]

    @staticmethod
    def cmd_upgrade() -> List[str]:
        return ["apt-get", "upgrade", "-y"]

    @staticmethod
    def cmd_install(package_name: str) -> List[str]:
        return ["apt-get", "install", "-y", package_name]

    @staticmethod
    def cmd_reinstall(package_name: str) -> List[str]:
        return ["apt-get", "install", "--reinstall", "-y", package_name]

    @staticmethod
    def cmd_remove(package_name: str) -> List[str]:
        return ["apt-get", "remove", "-y", package_name]

    @staticmethod
    def cmd_purge(package_name: str) -> List[str]:
        return ["apt-get", "purge", "-y", package_name]

    @staticmethod
    def cmd_autoremove() -> List[str]:
        return ["apt-get", "autoremove", "-y"]

    @staticmethod
    def cmd_clean() -> List[str]:
        return ["apt-get", "clean"]
