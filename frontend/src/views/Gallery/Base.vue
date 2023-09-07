<script setup>
import { ref, inject, onMounted, onBeforeUnmount } from "vue";
import { onBeforeRouteUpdate, useRoute } from "vue-router";
import { storeToRefs } from "pinia";
import { fetchRomsApi } from "@/services/api";
import { views, normalizeString } from "@/utils/utils";
import storeGalleryFilter from "@/stores/galleryFilter";
import storeGalleryView from "@/stores/galleryView";
import storeRoms from "@/stores/roms";
import GalleryAppBar from "@/components/GalleryAppBar/Base.vue";
import GameCard from "@/components/Game/Card/Base.vue";
import GameDataTable from "@/components/Game/DataTable/Base.vue";
import SearchRomDialog from "@/components/Dialog/Rom/SearchRom.vue";
import UploadRomDialog from "@/components/Dialog/Rom/UploadRom.vue";
import EditRomDialog from "@/components/Dialog/Rom/EditRom.vue";
import DeleteRomDialog from "@/components/Dialog/Rom/DeleteRom.vue";
import LoadingDialog from "@/components/Dialog/Loading.vue";
import FabMenu from "@/components/FabMenu/Base.vue";

// Props
const route = useRoute();
const galleryView = storeGalleryView();
const galleryFilter = storeGalleryFilter();
const gettingRoms = ref(false);
const fabMenu = ref(false);
const scrolledToTop = ref(true);
const romsStore = storeRoms();
const {
  allRoms,
  filteredRoms,
  selectedRoms,
  searchRoms,
  cursor,
  searchCursor,
} = storeToRefs(romsStore);

// Event listeners bus
const emitter = inject("emitter");
emitter.on("filter", onFilterChange);
emitter.on("openFabMenu", (open) => {
  fabMenu.value = open;
});

// Functions
async function fetchRoms(platform) {
  const isFiltered = normalizeString(galleryFilter.filter).trim() != "";

  if (
    (searchCursor.value === null && isFiltered) ||
    (cursor.value === null && !isFiltered) ||
    gettingRoms.value
  )
    return;

  gettingRoms.value = true;
  emitter.emit("showLoadingDialog", {
    loading: gettingRoms.value,
    scrim: false,
  });

  await fetchRomsApi({
    platform: platform,
    cursor: isFiltered ? searchCursor.value : cursor.value,
    searchTerm: normalizeString(galleryFilter.filter),
  })
    .then((response) => {
      if (isFiltered) {
        searchCursor.value = response.data.next_page;
        romsStore.setSearch([...searchRoms.value, ...response.data.items]);
        romsStore.setFiltered(searchRoms.value);
      } else {
        cursor.value = response.data.next_page;
        romsStore.set([...allRoms.value, ...response.data.items]);
        romsStore.setFiltered(allRoms.value);
      }
    })
    .catch((error) => {
      console.error(`Couldn't fetch roms for ${platform}: ${error}`);
    })
    .finally(() => {
      gettingRoms.value = false;
      emitter.emit("showLoadingDialog", {
        loading: gettingRoms.value,
        scrim: false,
      });
    });
}

function onFilterChange() {
  searchCursor.value = "";
  romsStore.setSearch([]);

  if (galleryFilter.filter === "") {
    romsStore.setFiltered(allRoms.value);
    return;
  }

  fetchRoms(route.params.platform);
}

function onScroll() {
  const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
  scrolledToTop.value = scrollTop === 0;

  if (!cursor.value && !searchCursor.value) return;

  const scrollOffset = 60;
  if (scrollTop + clientHeight + scrollOffset >= scrollHeight) {
    fetchRoms(route.params.platform);
  }
}

function toTop() {
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: "smooth",
  });
}

function selectRom({ event, index, selected }) {
  if (event.shiftKey) {
    const [start, end] = [romsStore.lastSelectedIndex, index].sort(
      (a, b) => a - b
    );
    if (selected) {
      for (let i = start + 1; i < end; i++) {
        romsStore.addToSelection(filteredRoms.value[i]);
      }
    } else {
      for (let i = start; i <= end; i++) {
        romsStore.removeFromSelection(filteredRoms.value[i]);
      }
    }
    romsStore.updateLastSelected(selected ? index : index - 1);
  } else {
    romsStore.updateLastSelected(index);
  }
}

onMounted(async () => {
  if (filteredRoms.value.length == 0) {
    fetchRoms(route.params.platform);
  }
});

onBeforeUnmount(() => {
  romsStore.resetSelection();
});

onBeforeRouteUpdate(async (to, _) => {
  cursor.value = "";
  searchCursor.value = "";
  romsStore.reset();
  fetchRoms(to.params.platform);
});
</script>

<template>
  <gallery-app-bar />
  <template v-if="filteredRoms.length > 0">
    <v-row no-gutters v-scroll="onScroll">
      <!-- Gallery cards view -->
      <v-col
        v-show="galleryView.current != 2"
        v-for="rom in filteredRoms"
        :key="rom.id"
        :cols="views[galleryView.current]['size-cols']"
        :xs="views[galleryView.current]['size-xs']"
        :sm="views[galleryView.current]['size-sm']"
        :md="views[galleryView.current]['size-md']"
        :lg="views[galleryView.current]['size-lg']"
      >
        <game-card
          :rom="rom"
          :index="filteredRoms.indexOf(rom)"
          :selected="selectedRoms.includes(rom)"
          @selectRom="selectRom"
        />
      </v-col>

      <!-- Gallery list view -->
      <v-col v-show="galleryView.current == 2">
        <game-data-table />
      </v-col>
    </v-row>
  </template>

  <!-- Empty gallery message -->
  <template v-if="filteredRoms.length == 0 && !gettingRoms">
    <v-row class="align-center justify-center" no-gutters>
      <v-col cols="6" md="2">
        <div class="mt-16">
          Feels empty here... <v-icon>mdi-emoticon-sad</v-icon>
        </div>
      </v-col>
    </v-row>
  </template>

  <v-layout-item
    v-scroll="onScroll"
    class="text-end"
    :model-value="true"
    position="bottom"
    size="88"
  >
    <div class="ma-4">
      <v-scroll-y-reverse-transition>
        <v-btn
          id="scrollToTop"
          v-show="!scrolledToTop"
          color="primary"
          elevation="8"
          icon
          class="mr-2"
          size="large"
          @click="toTop"
          ><v-icon color="romm-accent-2">mdi-chevron-up</v-icon></v-btn
        >
      </v-scroll-y-reverse-transition>
      <v-menu
        location="top"
        v-model="fabMenu"
        :transition="
          fabMenu ? 'scroll-y-reverse-transition' : 'scroll-y-transition'
        "
      >
        <template v-slot:activator="{ props }">
          <v-fab-transition>
            <v-btn
              v-show="romsStore._selectedIDs.length > 0"
              color="romm-accent-1"
              v-bind="props"
              elevation="8"
              icon
              size="large"
              >{{ romsStore._selectedIDs.length }}</v-btn
            >
          </v-fab-transition>
        </template>

        <fab-menu />
      </v-menu>
    </div>
  </v-layout-item>

  <search-rom-dialog />
  <upload-rom-dialog />
  <edit-rom-dialog />
  <delete-rom-dialog />
  <loading-dialog />
</template>

<style scoped>
.game-card.game-selected {
  border: 2px solid rgba(var(--v-theme-romm-accent-2));
  padding: 0;
}
#scrollToTop {
  border: 1px solid rgba(var(--v-theme-romm-accent-2));
}
</style>