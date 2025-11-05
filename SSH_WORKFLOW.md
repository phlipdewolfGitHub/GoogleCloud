# Manual SSH Workflow for Gurobi on Google Cloud

This guide walks you through manually creating a VM, installing Gurobi, running your optimization, and cleaning up.

**When to use this approach:**
- Learning and experimentation
- Debugging optimization problems
- Interactive development
- Running multiple optimizations on the same VM

**When to use automated approach instead:**
- Running optimizations regularly
- Want to minimize costs automatically
- One-off optimization runs

## Prerequisites

1. Google Cloud SDK installed and authenticated
2. A Google Cloud project with billing enabled
3. Gurobi license (WLS recommended for cloud usage)

## Step-by-Step Workflow

### 1. Create a VM Instance

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create VM (adjust machine-type as needed)
gcloud compute instances create gurobi-vm \
  --zone=us-central1-a \
  --machine-type=n2-standard-8 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-standard
```

**Machine type recommendations:**
- `n2-standard-8` - 8 vCPUs, 32GB RAM (~$0.39/hour) - Good starting point
- `n2-standard-16` - 16 vCPUs, 64GB RAM (~$0.78/hour) - Large models
- `n2-highcpu-32` - 32 vCPUs, 32GB RAM (~$1.18/hour) - Highly parallel
- `c2-standard-30` - 30 vCPUs, 120GB RAM (~$1.58/hour) - Memory-intensive

**Cost-saving tip:** Add `--preemptible` flag for 80% discount (VM can be interrupted)

### 2. Connect to VM

```bash
# SSH into the VM
gcloud compute ssh gurobi-vm --zone=us-central1-a
```

You're now on the VM! All following commands run on the VM.

### 3. Setup Gurobi on VM

**Option A: Use the setup script (recommended)**

Exit SSH, then from your local machine:

```bash
# Upload setup script
gcloud compute scp setup_vm.sh gurobi-vm:~/ --zone=us-central1-a

# SSH back in
gcloud compute ssh gurobi-vm --zone=us-central1-a

# Run setup script
chmod +x setup_vm.sh
./setup_vm.sh
```

**Option B: Manual setup**

If you prefer to understand each step:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python
sudo apt-get install -y python3 python3-pip python3-venv wget

# Create workspace
mkdir ~/gurobi_workspace
cd ~/gurobi_workspace

# Download Gurobi (check gurobi.com for latest version)
wget https://packages.gurobi.com/11.0/gurobi11.0.0_linux64.tar.gz
tar -xzf gurobi11.0.0_linux64.tar.gz
rm gurobi11.0.0_linux64.tar.gz

# Set environment variables
echo 'export GUROBI_HOME="$HOME/gurobi_workspace/gurobi1100/linux64"' >> ~/.bashrc
echo 'export PATH="${PATH}:${GUROBI_HOME}/bin"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"' >> ~/.bashrc
source ~/.bashrc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install gurobipy
cd $GUROBI_HOME
python3 setup.py install

# Test installation
python3 -c "import gurobipy; print('Gurobi installed successfully!')"
```

### 4. Configure Gurobi License

If using Gurobi WLS (Web License Service) - recommended for students:

```bash
# Set license environment variables (on the VM)
export WLSACCESSID="your-access-id-here"
export WLSSECRET="your-secret-key-here"
export LICENSEID="your-license-id-here"

# Make permanent by adding to .bashrc
echo 'export WLSACCESSID="your-access-id-here"' >> ~/.bashrc
echo 'export WLSSECRET="your-secret-key-here"' >> ~/.bashrc
echo 'export LICENSEID="your-license-id-here"' >> ~/.bashrc
```

**Get WLS license:**
1. Go to https://www.gurobi.com/academia/
2. Register with your .edu email
3. Get free WLS Academic license
4. You'll receive the three credentials above

### 5. Upload Your Optimization Code

Exit SSH, then from your local machine:

```bash
# Upload your Python script
gcloud compute scp your_optimization.py gurobi-vm:~/gurobi_workspace/ --zone=us-central1-a

# Upload any data files if needed
gcloud compute scp data.csv gurobi-vm:~/gurobi_workspace/ --zone=us-central1-a
```

Or upload the example:

```bash
gcloud compute scp example_mip_problem.py gurobi-vm:~/gurobi_workspace/ --zone=us-central1-a
```

### 6. Run Your Optimization

SSH back in:

```bash
gcloud compute ssh gurobi-vm --zone=us-central1-a
```

Then run your code:

```bash
# Activate environment
cd ~/gurobi_workspace
source venv/bin/activate

# Run optimization
python3 your_optimization.py

# Or run the example
python3 example_mip_problem.py
```

**Pro tip:** Use `screen` or `tmux` for long-running jobs so you can disconnect:

```bash
# Install screen
sudo apt-get install -y screen

# Start screen session
screen -S optimization

# Run your code
python3 your_optimization.py

# Detach: Press Ctrl+A, then D
# Reconnect later: screen -r optimization
```

### 7. Download Results

Exit SSH, then from your local machine:

```bash
# Download result files
gcloud compute scp gurobi-vm:~/gurobi_workspace/*.sol ./results/ --zone=us-central1-a
gcloud compute scp gurobi-vm:~/gurobi_workspace/*.log ./results/ --zone=us-central1-a

# Or download everything
gcloud compute scp --recurse gurobi-vm:~/gurobi_workspace/results/ ./results/ --zone=us-central1-a
```

### 8. Stop or Delete the VM

**IMPORTANT:** Don't forget this step or you'll keep paying!

**Option A: Stop the VM (saves disk, can restart later)**

```bash
gcloud compute instances stop gurobi-vm --zone=us-central1-a
```

To restart later:

```bash
gcloud compute instances start gurobi-vm --zone=us-central1-a
```

**Option B: Delete the VM (no charges, but must setup again)**

```bash
gcloud compute instances delete gurobi-vm --zone=us-central1-a
```

## Quick Reference Commands

```bash
# Check VM status
gcloud compute instances list

# SSH into VM
gcloud compute ssh gurobi-vm --zone=us-central1-a

# Upload file to VM
gcloud compute scp local_file.py gurobi-vm:~/path/ --zone=us-central1-a

# Download file from VM
gcloud compute scp gurobi-vm:~/path/file.txt ./ --zone=us-central1-a

# Stop VM (keeps disk)
gcloud compute instances stop gurobi-vm --zone=us-central1-a

# Start stopped VM
gcloud compute instances start gurobi-vm --zone=us-central1-a

# Delete VM (removes everything)
gcloud compute instances delete gurobi-vm --zone=us-central1-a

# Check current costs
gcloud beta billing accounts list
```

## Monitoring Costs

1. Go to https://console.cloud.google.com/billing
2. Select your project
3. View "Reports" to see spending
4. Set up budget alerts (recommended!)

## Troubleshooting

### SSH connection refused
VM might still be booting. Wait 1-2 minutes and try again.

### "No license found" error
Make sure to export WLS credentials or install a license on the VM.

### Out of memory errors
Try a VM with more RAM (e.g., `n2-highmem-8` or `n2-standard-16`)

### Slow optimization
Try a VM with more vCPUs (e.g., `n2-standard-16` or `n2-highcpu-32`)

### Permission denied
```bash
# Re-authenticate
gcloud auth login
```

## Running Multiple Optimizations

If you're running many optimizations, you can keep the VM running:

```bash
# Keep VM running and process multiple files
for file in problem1.py problem2.py problem3.py; do
  gcloud compute scp $file gurobi-vm:~/gurobi_workspace/ --zone=us-central1-a
  gcloud compute ssh gurobi-vm --zone=us-central1-a --command "cd ~/gurobi_workspace && source venv/bin/activate && python3 $file"
done

# Don't forget to stop the VM when completely done!
gcloud compute instances stop gurobi-vm --zone=us-central1-a
```

## Next Steps

- Try the automated workflow: `automated_gurobi_solver.py`
- Experiment with different VM sizes
- Set up budget alerts in Google Cloud Console
- Learn about preemptible VMs for even cheaper compute

## Tips for Students

1. **Use preemptible VMs** for development (much cheaper)
2. **Always stop/delete VMs** when not in use
3. **Set budget alerts** at $50, $100, $150 to track spending
4. **Start small** - A standard-8 VM is plenty powerful for most problems
5. **Use WLS license** - works from anywhere, no need to move licenses around
