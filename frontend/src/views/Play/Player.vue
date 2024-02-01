<script setup lang="ts">
import { ref, onBeforeUnmount } from "vue";
import stateApi from "@/services/api/state";
import saveApi, { saveApi as api } from "@/services/api/save";
import screenshotApi from "@/services/api/screenshot";
import type { Rom } from "@/stores/roms";
import { platformSlugEJSCoreMap } from "@/utils";
import type { SaveSchema, StateSchema } from "@/__generated__";

const props = defineProps<{
  rom: Rom;
  save: SaveSchema | null;
  state: StateSchema | null;
}>();
const saveRef = ref<SaveSchema | null>(props.save);
const stateRef = ref<StateSchema | null>(props.state);

onBeforeUnmount(() => {
  window.location.reload();
});

// Declare global variables for EmulatorJS
declare global {
  interface Window {
    EJS_core: string;
    EJS_player: string;
    EJS_pathtodata: string;
    EJS_color: string;
    EJS_defaultOptions: object;
    EJS_gameID: number;
    EJS_gameName: string;
    EJS_backgroundImage: string;
    EJS_gameUrl: string;
    EJS_loadStateURL: string | null;
    EJS_cheats: string;
    EJS_gamePatchUrl: string;
    EJS_netplayServer: string;
    EJS_alignStartButton: string;
    EJS_startOnLoaded: boolean;
    EJS_fullscreenOnLoaded: boolean;
    EJS_emulator: any;
    EJS_onGameStart: () => void;
    EJS_onSaveState: (args: { screenshot: File; state: File }) => void;
    EJS_onLoadState: () => void;
    EJS_onSaveSave: (args: { screenshot: File; save: File }) => void;
    EJS_onLoadSave: () => void;
  }
}

window.EJS_core = platformSlugEJSCoreMap[props.rom.platform_slug];
window.EJS_gameID = props.rom.id;
window.EJS_gameUrl = props.rom.download_path;
window.EJS_player = "#game";
window.EJS_pathtodata = "/assets/emulatorjs/";
window.EJS_color = "#A453FF";
window.EJS_alignStartButton = "center";
window.EJS_startOnLoaded = true;
window.EJS_backgroundImage = "/assets/emulatorjs/loading_black.png";
window.EJS_defaultOptions = { "save-state-location": "browser" };
if (props.rom.name) window.EJS_gameName = props.rom.name;

function buildStateName(): string {
  const states = props.rom.states.map((s) => s.file_name);
  const romName = props.rom.file_name_no_ext.trim();
  let stateName = `${romName}.state.auto`;
  if (!states.includes(stateName)) return stateName;

  let i = 1;
  stateName = `${romName}.state1`;
  while (states.includes(stateName)) {
    i++;
    stateName = `${romName}.state${i}`;
  }

  return stateName;
}

function buildSaveName(): string {
  const saves = props.rom.saves.map((s) => s.file_name);
  const romName = props.rom.file_name_no_ext.trim();
  let saveName = `${romName}.srm`;
  if (!saves.includes(saveName)) return saveName;

  let i = 2;
  saveName = `${romName} (${i}).srm`;
  while (saves.includes(saveName)) {
    i++;
    saveName = `${romName} (${i}).srm`;
  }

  return saveName;
}

async function fetchState(): Promise<Uint8Array> {
  if (stateRef.value) {
    const { data } = await api.get(
      stateRef.value.download_path.replace("/api", ""),
      { responseType: "arraybuffer" }
    );
    return new Uint8Array(data);
  } else if (window.EJS_emulator.saveInBrowserSupported()) {
    const data = await window.EJS_emulator.storage.states.get(
      window.EJS_emulator.getBaseFileName() + ".state"
    );
    return data;
  }
  return new Uint8Array();
}

window.EJS_onLoadState = async function () {
  const state = await fetchState();
  window.EJS_emulator.gameManager.loadState(state);
  window.EJS_emulator.displayMessage("LOADED FROM ROMM");
};

window.EJS_onSaveState = function ({
  state,
  screenshot,
}: {
  screenshot: BlobPart;
  state: BlobPart;
}) {
  if (window.EJS_emulator.saveInBrowserSupported()) {
    window.EJS_emulator.storage.states.put(
      window.EJS_emulator.getBaseFileName() + ".state",
      state
    );
    window.EJS_emulator.displayMessage("SAVED TO ROMM");
  }
  if (stateRef.value) {
    stateApi
      .updateState({
        state: stateRef.value,
        file: new File([state], stateRef.value.file_name, {
          type: "application/octet-stream",
        }),
      })
      .then(({ data }) => {
        stateRef.value = data;
      });

    if (stateRef.value.screenshot) {
      screenshotApi
        .updateScreenshot({
          screenshot: stateRef.value.screenshot,
          file: new File([screenshot], stateRef.value.screenshot.file_name, {
            type: "application/octet-stream",
          }),
        })
        .then(({ data }) => {
          if (stateRef.value) stateRef.value.screenshot = data;
        });
    } else {
      screenshotApi
        .uploadScreenshots({
          rom: props.rom,
          screenshots: [
            new File([screenshot], `${buildStateName()}.png`, {
              type: "application/octet-stream",
            }),
          ],
        })
        .then(({ data }) => {
          if (stateRef.value) stateRef.value.screenshot = data.screenshots[0];
          props.rom.screenshots = data.screenshots;
          props.rom.url_screenshots = data.url_screenshots;
          props.rom.merged_screenshots = data.merged_screenshots;
        });
    }
  } else if (props.rom) {
    stateApi
      .uploadStates({
        rom: props.rom,
        emulator: platformSlugEJSCoreMap[props.rom.platform_slug],
        states: [
          new File([state], buildStateName(), {
            type: "application/octet-stream",
          }),
        ],
      })
      .then(({ data }) => {
        const allStates = data.states.sort(
          (a: StateSchema, b: StateSchema) => a.id - b.id
        );
        if (props.rom) props.rom.states = allStates;
        stateRef.value = allStates.pop() ?? null;
      });

    screenshotApi
      .uploadScreenshots({
        rom: props.rom,
        screenshots: [
          new File([screenshot], `${buildStateName()}.png`, {
            type: "application/octet-stream",
          }),
        ],
      })
      .then(({ data }) => {
        props.rom.screenshots = data.screenshots;
        props.rom.url_screenshots = data.url_screenshots;
        props.rom.merged_screenshots = data.merged_screenshots;
      });
  }
};

async function fetchSave(): Promise<Uint8Array> {
  if (saveRef.value) {
    const { data } = await api.get(
      saveRef.value.download_path.replace("/api", ""),
      { responseType: "arraybuffer" }
    );
    return new Uint8Array(data);
  }

  const file = await window.EJS_emulator.selectFile();
  return new Uint8Array(await file.arrayBuffer());
}

window.EJS_onLoadSave = async function () {
  const sav = await fetchSave();
  const FS = window.EJS_emulator.Module.FS;
  const path = window.EJS_emulator.gameManager.getSaveFilePath();
  const paths = path.split("/");
  let cp = "";
  for (let i = 0; i < paths.length - 1; i++) {
    if (paths[i] === "") continue;
    cp += "/" + paths[i];
    if (!FS.analyzePath(cp).exists) FS.mkdir(cp);
  }
  if (FS.analyzePath(path).exists) FS.unlink(path);
  FS.writeFile(path, sav);
  window.EJS_emulator.gameManager.loadSaveFiles();
};

window.EJS_onSaveSave = function ({
  save,
  screenshot,
}: {
  save: BlobPart;
  screenshot: BlobPart;
}) {
  if (saveRef.value) {
    saveApi
      .updateSave({
        save: saveRef.value,
        file: new File([save], saveRef.value.file_name, {
          type: "application/octet-stream",
        }),
      })
      .then(({ data }) => {
        saveRef.value = data;
      });

    if (saveRef.value.screenshot) {
      screenshotApi
        .updateScreenshot({
          screenshot: saveRef.value.screenshot,
          file: new File([screenshot], saveRef.value.screenshot.file_name, {
            type: "application/octet-stream",
          }),
        })
        .then(({ data }) => {
          if (saveRef.value) saveRef.value.screenshot = data;
        });
    } else {
      screenshotApi
        .uploadScreenshots({
          rom: props.rom,
          screenshots: [
            new File([screenshot], `${buildSaveName()}.png`, {
              type: "application/octet-stream",
            }),
          ],
        })
        .then(({ data }) => {
          if (saveRef.value) saveRef.value.screenshot = data.screenshots[0];
          props.rom.screenshots = data.screenshots;
          props.rom.url_screenshots = data.url_screenshots;
          props.rom.merged_screenshots = data.merged_screenshots;
        });
    }
  } else if (props.rom) {
    saveApi
      .uploadSaves({
        rom: props.rom,
        emulator: platformSlugEJSCoreMap[props.rom.platform_slug],
        saves: [
          new File([save], buildSaveName(), {
            type: "application/octet-stream",
          }),
        ],
      })
      .then(({ data }) => {
        const allSaves = data.saves.sort(
          (a: SaveSchema, b: SaveSchema) => a.id - b.id
        );
        if (props.rom) props.rom.saves = allSaves;
        saveRef.value = allSaves.pop() ?? null;
      });

    screenshotApi
      .uploadScreenshots({
        rom: props.rom,
        screenshots: [
          new File([screenshot], `${buildSaveName()}.png`, {
            type: "application/octet-stream",
          }),
        ],
      })
      .then(({ data }) => {
        props.rom.screenshots = data.screenshots;
        props.rom.url_screenshots = data.url_screenshots;
        props.rom.merged_screenshots = data.merged_screenshots;
      });
  }
};

window.EJS_onGameStart = async () => {
  saveRef.value = props.save;
  stateRef.value = props.state;

  setTimeout(() => {
    if (stateRef.value) window.EJS_onLoadState();
    if (saveRef.value) window.EJS_onLoadSave();
  }, 10);
};
</script>

<template>
  <div id="game"></div>
</template>

<!-- Other config options: https://emulatorjs.org/docs/Options.html -->

<!-- window.EJS_biosUrl; -->
<!-- window.EJS_VirtualGamepadSettings; -->
<!-- window.EJS_cheats; -->
<!-- window.EJS_gamePatchUrl; -->
<!-- window.EJS_gameParentUrl; -->
<!-- window.EJS_netplayServer; -->