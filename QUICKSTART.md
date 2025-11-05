# Quick Start Guide

Get up and running with Gurobi on Google Cloud in 15 minutes!

## Step 1: Install Google Cloud SDK

If you haven't already:

**Mac:**
```bash
brew install google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
Download from https://cloud.google.com/sdk/docs/install

## Step 2: Setup Google Cloud

```bash
# Login
gcloud auth login

# Set your project (replace with your project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable Compute Engine
gcloud services enable compute.googleapis.com

# Authenticate for Python SDK
gcloud auth application-default login
```

**Don't have a project?** Create one:
```bash
gcloud projects create gurobi-optimization --name="Gurobi Optimization"
gcloud config set project gurobi-optimization
```

## Step 3: Get Gurobi License (Free for Students!)

1. Go to https://www.gurobi.com/academia/academic-program-and-licenses/
2. Click "Register" and use your .edu email
3. After registration, request a **WLS Academic License**
4. You'll receive three credentials: WLSACCESSID, WLSSECRET, LICENSEID

Set them in your environment:
```bash
export WLSACCESSID="your-access-id"
export WLSSECRET="your-secret"
export LICENSEID="your-license-id"
```

**Make it permanent:** Add to your `~/.bashrc` or `~/.zshrc`

## Step 4: Choose Your Path

### Path A: Automated (Recommended for First Try)

Run everything with one command:

```bash
# Install Python dependencies
pip install google-cloud-compute

# Run the automated solver with the example problem
python automated_gurobi_solver.py \
  --project YOUR_PROJECT_ID \
  --script example_mip_problem.py
```

That's it! The script will:
- Create a VM
- Install Gurobi
- Run your optimization
- Download results
- Delete the VM (saving you money!)

### Path B: Manual SSH (Recommended for Learning)

Follow the detailed guide in `SSH_WORKFLOW.md`

## Step 5: Customize for Your Problem

Replace `example_mip_problem.py` with your own Gurobi code:

```python
import gurobipy as gp
from gurobipy import GRB

# Create model
model = gp.Model("my_problem")

# Add your variables, constraints, objective
# ...

# Solve
model.optimize()

# Print results
if model.Status == GRB.OPTIMAL:
    print(f"Optimal objective: {model.ObjVal}")
```

Then run it on the cloud:

```bash
python automated_gurobi_solver.py \
  --project YOUR_PROJECT_ID \
  --script my_optimization.py \
  --machine-type n2-standard-16  # More powerful if needed
```

## Common Issues

**"Permission denied" errors:**
```bash
gcloud auth login
gcloud auth application-default login
```

**"Project not found":**
```bash
gcloud projects list  # See your projects
gcloud config set project YOUR_PROJECT_ID
```

**Gurobi license errors:**
Make sure you exported WLSACCESSID, WLSSECRET, and LICENSEID

**VM creation fails:**
Check quotas in Google Cloud Console → IAM & Admin → Quotas

## What's Next?

1. ✅ Run the example problem
2. ✅ Adapt it to your optimization problem
3. ✅ Try different VM sizes (see README.md for cost estimates)
4. ✅ Set up budget alerts in Google Cloud Console
5. ✅ Star this repo if it helped! 🌟

## Need Help?

- **Read the full docs:** `README.md`
- **Manual workflow:** `SSH_WORKFLOW.md`
- **Gurobi docs:** https://www.gurobi.com/documentation/
- **Google Cloud docs:** https://cloud.google.com/compute/docs

## Cost Reminder

You have $300 in credits. A typical optimization run costs:
- Small VM (8 vCPUs): ~$0.39/hour = ~$0.01/minute
- Large VM (30 vCPUs): ~$1.58/hour = ~$0.03/minute

**Always** stop or delete VMs when not in use!

```bash
# List running VMs
gcloud compute instances list

# Stop a VM
gcloud compute instances stop VM_NAME --zone=us-central1-a

# Delete a VM
gcloud compute instances delete VM_NAME --zone=us-central1-a
```

Happy optimizing! 🚀
