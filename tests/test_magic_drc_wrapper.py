from pathlib import Path
import os
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_magic_drc_tcl_variable_survives_strict_shell_expansion(tmp_path: Path) -> None:
    pdk_root = tmp_path / "sky130A"
    magic_dir = pdk_root / "libs.tech" / "magic"
    magic_dir.mkdir(parents=True)
    (magic_dir / "sky130A.magicrc").write_text("# test rc\n", encoding="utf-8")

    gds = tmp_path / "test.gds"
    gds.write_bytes(b"test")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_magic = bin_dir / "magic"
    fake_magic.write_text("#!/usr/bin/env bash\ncat\n", encoding="utf-8")
    fake_magic.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    result = subprocess.run(
        [
            str(ROOT / "scripts" / "run_magic_drc.sh"),
            "--open-pdks-root",
            str(pdk_root),
            "--gds",
            str(gds),
            "--top",
            "TEST",
            "--out-dir",
            str(tmp_path / "out"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    log = (tmp_path / "out" / "raw_logs" / "TEST.magic_drc.log").read_text(
        encoding="utf-8"
    )
    assert "puts $violation" in log
