#!/usr/bin/env python3
"""
Automated Gurobi Solver with Google Cloud VM Management

This script automates the entire workflow:
1. Creates a Google Cloud VM instance
2. Sets up Gurobi on the VM
3. Uploads your optimization code
4. Runs the optimization
5. Downloads results
6. Deletes the VM (to save money!)

Usage:
    python automated_gurobi_solver.py --project YOUR_PROJECT_ID --script your_code.py

Requirements:
    pip install google-cloud-compute
"""

import argparse
import time
import sys
import os
import subprocess
from pathlib import Path


class GurobiCloudSolver:
    """Manages VM lifecycle for running Gurobi optimization"""

    def __init__(self, project_id, zone="us-central1-a", machine_type="n2-standard-8"):
        self.project_id = project_id
        self.zone = zone
        self.machine_type = machine_type
        self.instance_name = f"gurobi-solver-{int(time.time())}"
        self.setup_script_path = Path(__file__).parent / "setup_vm.sh"

        # Gurobi WLS license (set these in environment variables)
        self.wls_access_id = os.environ.get("WLSACCESSID", "")
        self.wls_secret = os.environ.get("WLSSECRET", "")
        self.license_id = os.environ.get("LICENSEID", "")

    def create_vm(self):
        """Create a Google Cloud VM instance"""
        print("="*70)
        print(f"Creating VM instance: {self.instance_name}")
        print(f"Machine type: {self.machine_type}")
        print(f"Zone: {self.zone}")
        print("="*70)

        # First, ensure default SSH firewall rule exists
        print("Checking firewall rules...")
        firewall_check = subprocess.run(
            ["gcloud", "compute", "firewall-rules", "describe", "default-allow-ssh",
             "--project", self.project_id],
            capture_output=True,
            text=True
        )

        if firewall_check.returncode != 0:
            # Create SSH firewall rule
            print("Creating SSH firewall rule...")
            subprocess.run(
                ["gcloud", "compute", "firewall-rules", "create", "default-allow-ssh",
                 "--project", self.project_id,
                 "--allow", "tcp:22",
                 "--source-ranges", "0.0.0.0/0",
                 "--description", "Allow SSH from anywhere"],
                capture_output=True
            )
            print("✓ Firewall rule created")
        else:
            print("✓ Firewall rule exists")

        create_cmd = [
            "gcloud", "compute", "instances", "create", self.instance_name,
            "--project", self.project_id,
            "--zone", self.zone,
            "--machine-type", self.machine_type,
            "--image-family", "ubuntu-2204-lts",
            "--image-project", "ubuntu-os-cloud",
            "--boot-disk-size", "20GB",
            "--boot-disk-type", "pd-standard",
            "--metadata", "enable-oslogin=FALSE",
            "--scopes", "https://www.googleapis.com/auth/cloud-platform",
        ]

        try:
            result = subprocess.run(create_cmd, check=True, capture_output=True, text=True)
            print("✓ VM created successfully")
            print()
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create VM: {e.stderr}")
            return False

    def wait_for_vm_ready(self, max_wait=300):
        """Wait for VM to be ready for SSH connections"""
        print("Waiting for VM to be ready for SSH...")
        print("(This typically takes 1-3 minutes)")
        start_time = time.time()
        last_error = None

        while time.time() - start_time < max_wait:
            try:
                # Try a simple SSH command
                test_cmd = [
                    "gcloud", "compute", "ssh", self.instance_name,
                    "--project", self.project_id,
                    "--zone", self.zone,
                    "--command", "echo ready",
                    "--ssh-flag=-o", "--ssh-flag=StrictHostKeyChecking=no",
                    "--ssh-flag=-o", "--ssh-flag=ConnectTimeout=10"
                ]
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=20)

                if result.returncode == 0 and "ready" in result.stdout:
                    print("✓ VM is ready")
                    print()
                    return True
                else:
                    last_error = result.stderr
            except subprocess.TimeoutExpired:
                last_error = "SSH connection timed out"
            except Exception as e:
                last_error = str(e)

            elapsed = int(time.time() - start_time)
            print(f"  Still waiting... ({elapsed}s elapsed)", end='\r')
            time.sleep(10)

        print()
        print("✗ VM did not become ready in time")
        if last_error:
            print(f"Last error: {last_error[:200]}")
        return False

    def setup_gurobi_on_vm(self):
        """Upload and run setup script on VM"""
        print("="*70)
        print("Setting up Gurobi on VM")
        print("="*70)

        # Upload setup script
        print("Uploading setup script...")
        scp_cmd = [
            "gcloud", "compute", "scp",
            str(self.setup_script_path),
            f"{self.instance_name}:~/setup_vm.sh",
            "--project", self.project_id,
            "--zone", self.zone,
        ]

        try:
            subprocess.run(scp_cmd, check=True, capture_output=True)
            print("✓ Setup script uploaded")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to upload setup script: {e.stderr}")
            return False

        # Run setup script
        print("Running setup script (this may take 5-10 minutes)...")
        print()

        ssh_cmd = [
            "gcloud", "compute", "ssh", self.instance_name,
            "--project", self.project_id,
            "--zone", self.zone,
            "--command", "chmod +x ~/setup_vm.sh && ~/setup_vm.sh"
        ]

        try:
            subprocess.run(ssh_cmd, check=True)
            print()
            print("✓ Gurobi setup complete")
            print()
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Setup script failed")
            return False

    def upload_and_run_script(self, local_script_path):
        """Upload user's optimization script and run it"""
        print("="*70)
        print("Running Optimization")
        print("="*70)

        # Upload user script
        print(f"Uploading {local_script_path}...")
        scp_cmd = [
            "gcloud", "compute", "scp",
            local_script_path,
            f"{self.instance_name}:~/gurobi_workspace/user_code.py",
            "--project", self.project_id,
            "--zone", self.zone,
        ]

        try:
            subprocess.run(scp_cmd, check=True, capture_output=True)
            print("✓ Script uploaded")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to upload script: {e.stderr}")
            return False

        # Prepare license environment variables
        license_env = ""
        if self.wls_access_id and self.wls_secret and self.license_id:
            license_env = (
                f"export WLSACCESSID='{self.wls_access_id}' && "
                f"export WLSSECRET='{self.wls_secret}' && "
                f"export LICENSEID='{self.license_id}' && "
            )
            print("✓ Gurobi WLS license configured")
        else:
            print("⚠ Warning: No Gurobi WLS license found in environment variables")
            print("  Set WLSACCESSID, WLSSECRET, and LICENSEID if needed")

        # Run optimization
        print()
        print("Starting optimization (output will stream below)...")
        print("="*70)
        print()

        run_cmd = (
            f"{license_env}"
            f"~/gurobi_workspace/run_optimization.sh"
        )

        ssh_cmd = [
            "gcloud", "compute", "ssh", self.instance_name,
            "--project", self.project_id,
            "--zone", self.zone,
            "--command", run_cmd
        ]

        try:
            # Stream output in real-time
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                print(line, end='')

            process.wait()

            print()
            print("="*70)

            if process.returncode == 0:
                print("✓ Optimization completed successfully")
                print()
                return True
            else:
                print("✗ Optimization failed")
                return False

        except Exception as e:
            print(f"✗ Error running optimization: {e}")
            return False

    def download_results(self, output_dir="./results"):
        """Download any output files from the VM"""
        print("="*70)
        print("Downloading Results")
        print("="*70)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Try to download common output files
        output_files = [
            "*.sol",  # Gurobi solution files
            "*.log",  # Log files
            "*.lp",   # LP files
            "*.mps",  # MPS files
            "*.json", # JSON results
            "*.csv",  # CSV results
        ]

        downloaded_any = False

        for pattern in output_files:
            try:
                scp_cmd = [
                    "gcloud", "compute", "scp",
                    f"{self.instance_name}:~/gurobi_workspace/{pattern}",
                    str(output_path),
                    "--project", self.project_id,
                    "--zone", self.zone,
                ]
                result = subprocess.run(scp_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✓ Downloaded {pattern}")
                    downloaded_any = True
            except Exception:
                pass

        if not downloaded_any:
            print("No output files found to download")
            print("(This is normal if your script doesn't save files)")

        print()
        return True

    def delete_vm(self):
        """Delete the VM instance to stop charges"""
        print("="*70)
        print("Cleaning Up")
        print("="*70)

        delete_cmd = [
            "gcloud", "compute", "instances", "delete", self.instance_name,
            "--project", self.project_id,
            "--zone", self.zone,
            "--quiet"  # Don't prompt for confirmation
        ]

        try:
            subprocess.run(delete_cmd, check=True, capture_output=True)
            print(f"✓ VM {self.instance_name} deleted")
            print("✓ No further charges will accrue")
            print()
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to delete VM: {e.stderr}")
            print(f"⚠ Please manually delete the VM to avoid charges:")
            print(f"  gcloud compute instances delete {self.instance_name} --zone {self.zone}")
            return False

    def run_full_workflow(self, script_path):
        """Execute the complete workflow"""
        start_time = time.time()

        print("\n")
        print("="*70)
        print("GUROBI CLOUD SOLVER - AUTOMATED WORKFLOW")
        print("="*70)
        print(f"Project: {self.project_id}")
        print(f"Script: {script_path}")
        print(f"VM: {self.instance_name}")
        print("="*70)
        print("\n")

        try:
            # Step 1: Create VM
            if not self.create_vm():
                return False

            # Step 2: Wait for VM to be ready
            if not self.wait_for_vm_ready():
                self.delete_vm()
                return False

            # Step 3: Setup Gurobi
            if not self.setup_gurobi_on_vm():
                self.delete_vm()
                return False

            # Step 4: Run optimization
            if not self.upload_and_run_script(script_path):
                self.delete_vm()
                return False

            # Step 5: Download results
            self.download_results()

            # Step 6: Cleanup
            self.delete_vm()

            total_time = time.time() - start_time

            print("="*70)
            print("WORKFLOW COMPLETE!")
            print("="*70)
            print(f"Total time: {total_time/60:.1f} minutes")
            print("="*70)
            print()

            return True

        except KeyboardInterrupt:
            print("\n\n⚠ Workflow interrupted by user")
            print("Cleaning up...")
            self.delete_vm()
            return False
        except Exception as e:
            print(f"\n\n✗ Unexpected error: {e}")
            print("Cleaning up...")
            self.delete_vm()
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Run Gurobi optimization on Google Cloud VM"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Google Cloud project ID"
    )
    parser.add_argument(
        "--script",
        default="example_mip_problem.py",
        help="Path to your Python optimization script (default: example_mip_problem.py)"
    )
    parser.add_argument(
        "--zone",
        default="us-central1-a",
        help="Google Cloud zone (default: us-central1-a)"
    )
    parser.add_argument(
        "--machine-type",
        default="n2-standard-8",
        help="VM machine type (default: n2-standard-8)"
    )

    args = parser.parse_args()

    # Validate script exists
    if not Path(args.script).exists():
        print(f"✗ Error: Script not found: {args.script}")
        sys.exit(1)

    # Check for Gurobi license
    if not (os.environ.get("WLSACCESSID") and
            os.environ.get("WLSSECRET") and
            os.environ.get("LICENSEID")):
        print("⚠ Warning: Gurobi WLS license environment variables not found")
        print("  Set these if your script needs a Gurobi license:")
        print("    export WLSACCESSID='your-access-id'")
        print("    export WLSSECRET='your-secret'")
        print("    export LICENSEID='your-license-id'")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Create solver and run
    solver = GurobiCloudSolver(
        project_id=args.project,
        zone=args.zone,
        machine_type=args.machine_type
    )

    success = solver.run_full_workflow(args.script)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
