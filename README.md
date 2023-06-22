# playground-app



1. Install Python requirements
```
virtualenv -p /usr/bin/python3 grpc
source grpc/bin/activate
pip install -r requirements.txt 
```

2. Download a solution and adapt `pathSolutionZip` in exampleObjectModels.py accordingly.

3. Run `python exampleObjectModels.py` to start at least one pipeline. You can see the pipeline running with `kubectl get ns`. The namespace with the pipeline name in the beginning will contain the running pipeline.

4. Run `python app.py` to start the playground app, which will be available at 127.0.0.1:5000


# Cleanup

To cleanup the namespaces, you can run 
```
python -m scripts.cleanup_all_solutions
```

Note that you can choose between namespaces by considering solution_folders or namespaces considering a regex which should match all namespace names created by the playground.
