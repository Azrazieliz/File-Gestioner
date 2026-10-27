using BepInEx;
using UnityEngine;

namespace FileGestioner.NativeRemote
{
    // Maintains Unity graphics updates on the isolated, noninteractive PC
    // desktop. Native Koikatsu Studio still provides all characters/mods.
    [BepInPlugin("com.filegestioner.nativebackground", "File Gestioner Native Background", "1.0.0")]
    public sealed class NativeBackground : BaseUnityPlugin
    {
        private void Awake()
        {
            Application.runInBackground = true;
            Logger.LogInfo("Native background rendering enabled.");
        }

        private void Update()
        {
            if (!Application.runInBackground)
                Application.runInBackground = true;
        }
    }
}
