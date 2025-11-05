# Gurobi Optimization on Google Cloud Compute Engine

This repository shows how to run Gurobi MIP (Mixed Integer Programming) optimization problems on Google Cloud VMs for short compute sessions.

## Why Use Google Cloud for Gurobi?

- **More powerful hardware**: Access VMs with 32+ cores and lots of RAM
- **Pay per minute**: Only pay when your VM is running (~$0.50-$2.00/hour for powerful machines)
- **$300 free credits**: Plenty for testing and student projects
- **No 24/7 cost**: Automatically start/stop VMs as needed

## Overview of Approaches

### Option 1: Automated Python Script (Recommended)
- **Best for**: Running optimizations frequently, saving money automatically
- One command starts VM → runs optimization → retrieves results → stops VM
- See: `automated_gurobi_solver.py`

### Option 2: Manual SSH Workflow
- **Best for**: Learning, debugging, interactive work
- Manually start VM, SSH in, run code, stop VM when done
- See: `SSH_WORKFLOW.md`

## Prerequisites

1. **Google Cloud Account** with $300 credits activated
2. **Google Cloud SDK** installed locally ([Install guide](https://cloud.google.com/sdk/docs/install))
3. **Gurobi License** - You need one of:
   - Free Academic License (if you're a student) - [Get here](https://www.gurobi.com/academia/academic-program-and-licenses/)
   - Gurobi WLS (Web License Service) - works anywhere
   - Note: Your license must work on the VM (WLS is easiest)

## Quick Start

### 1. Set Up Google Cloud Project

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create gurobi-optimization-project --name="Gurobi Optimization"

# Set as active project
gcloud config set project gurobi-optimization-project

# Enable Compute Engine API
gcloud services enable compute.googleapis.com
```

### 2. Test Locally First

```bash
# Install dependencies
pip install gurobipy google-cloud-compute

# Test the example MIP problem locally
python example_mip_problem.py
```

### 3. Choose Your Workflow

#### Option A: Automated (Recommended)
```bash
# Edit automated_gurobi_solver.py with your settings
python automated_gurobi_solver.py
```

#### Option B: Manual SSH
See `SSH_WORKFLOW.md` for step-by-step instructions.

## Cost Estimation

With $300 credit, here's what you can run:

| VM Type | vCPUs | RAM | Cost/hour | Hours available |
|---------|-------|-----|-----------|-----------------|
| n2-standard-8 | 8 | 32 GB | ~$0.39 | ~770 hours |
| n2-standard-16 | 16 | 64 GB | ~$0.78 | ~385 hours |
| n2-highcpu-32 | 32 | 32 GB | ~$1.18 | ~254 hours |
| c2-standard-30 | 30 | 120 GB | ~$1.58 | ~190 hours |

**Important**: Always stop VMs when not in use! A VM running 24/7 will burn through credits.

## Files in This Repo

- `README.md` - This file
- `example_mip_problem.py` - Sample Gurobi optimization problem
- `automated_gurobi_solver.py` - Automated VM lifecycle management
- `setup_vm.sh` - Script to install Gurobi on a fresh VM
- `SSH_WORKFLOW.md` - Manual SSH workflow guide
- `requirements.txt` - Python dependencies

## Gurobi License Setup

Your Gurobi code needs a license. **Best option for students**: Get a free WLS Academic license.

1. Go to [Gurobi Academic Program](https://www.gurobi.com/academia/academic-program-and-licenses/)
2. Register with your .edu email
3. Get a WLS license (works from any IP address, including cloud VMs)
4. Set environment variables:

```bash
export WLSACCESSID="your-access-id"
export WLSSECRET="your-secret-key"
export LICENSEID="your-license-id"
```

Add these to your `~/.bashrc` on the VM or pass them to your script.

## Tips for Saving Money

1. **Always stop VMs when done** - Use `gcloud compute instances stop VM_NAME`
2. **Use preemptible VMs** - 80% cheaper but can be interrupted (fine for <1 hour jobs)
3. **Choose the right VM size** - Start small, scale up if needed
4. **Monitor spending** - Check [Google Cloud Console](https://console.cloud.google.com/billing)

## Troubleshooting

### "Permission denied" errors
```bash
gcloud auth application-default login
```

### Gurobi license errors on VM
Make sure to export your WLS credentials on the VM before running Gurobi.

### VM won't start
Check quotas in Google Cloud Console → IAM → Quotas

## Next Steps

1. Follow Quick Start above
2. Run the example problem
3. Replace `example_mip_problem.py` with your own optimization model
4. Enjoy fast solves on powerful hardware!

## Resources

- [Google Cloud Compute Engine Docs](https://cloud.google.com/compute/docs)
- [Gurobi Python API](https://www.gurobi.com/documentation/quickstart.html)
- [Google Cloud Free Trial](https://cloud.google.com/free)
