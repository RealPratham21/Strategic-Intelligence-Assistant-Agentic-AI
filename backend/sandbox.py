import sys
import io
import os
import re
import matplotlib
# Use 'Agg' to ensure the backend doesn't try to open a GUI window
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class LogicSandbox:
    def __init__(self):
        # We pre-load data science libraries to make them instantly available to Gemini
        self.globals = {
            "plt": plt,
            "pd": pd,
            "np": np
        }
        self.locals = {}

    def run_code(self, code: str, output_filename: str | None = None):
        """
        Executes code dynamically and handles chart lifecycle.
        """
        # 1. Reset state for a clean execution
        plt.close('all') 
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        saved_files = []

        try:
            # 2. Execute the code string provided by the LLM
            exec(code, self.globals, self.locals)
            sys.stdout = old_stdout

            # 3. Detect files if the LLM explicitly used plt.savefig('filename.png')
            if "plt.savefig" in code:
                matches = re.findall(r"plt\.savefig\((?:'|\")([^'\"]+)(?:'|\")\)", code)
                for m in matches:
                    if os.path.exists(m):
                        saved_files.append(m)

            # 4. Auto-Save Fallback: If figures exist in memory but weren't saved to disk
            figs = plt.get_fignums()
            if figs and not saved_files:
                for i, fig_num in enumerate(figs, start=1):
                    if output_filename:
                        fname = output_filename if len(figs) == 1 else f"{os.path.splitext(output_filename)[0]}_{i}.png"
                    else:
                        fname = f"output_chart_{i}.png"
                    
                    plt.figure(fig_num)
                    plt.savefig(fname)
                    saved_files.append(fname)

            chart_status = f"Charts saved: {saved_files}" if saved_files else "No chart generated"

            return {
                "status": "success",
                "output": f"{output_buffer.getvalue().strip()}\n[{chart_status}]",
                "error": "",
                "files": saved_files
            }

        except Exception as e:
            sys.stdout = old_stdout
            return {
                "status": "error", 
                "output": output_buffer.getvalue().strip(), 
                "error": str(e), 
                "files": []
            }
        finally:
            # 5. Cleanup to prevent memory issues across multiple agent turns
            plt.close('all')