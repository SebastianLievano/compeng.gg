import { TabMenu } from "primereact/tabmenu";
import { Lab } from "../[courseSlug]/[offeringSlug]/page";
import { useState } from 'react';
import PrimeWrapper from "../components/primeWrapper";
import 'primeicons/primeicons.css';
import { Button } from "primereact/button";
import StudentTeamViewTab from "../studentView/components/student-team-view-tab";
import StaffTeamViewTab from "./components/staff-team-view-tab";


export interface StaffViewProps {
    courseName: string;
    labs: Lab[];
    courseSlug: string;
}

export default function StaffView(props: StaffViewProps){
    const {courseName, labs, courseSlug} = props;

    const [idx, setIdx] = useState<number>(0);

    const items = [
        // { label: 'Assignments', icon: 'pi pi-list-check'},
        // { label: 'Exercises', icon: 'pi pi-check-circle'},
        // { label: 'Tests', icon: 'pi pi-pencil'},
        { label: 'Course Settings', icon: 'pi pi-spin pi-cog',},
        { label: 'Students', icon: 'pi pi-spin pi-user'},
        { label: 'Teams', icon: 'pi pi-spin pi-users'}
        // test
    ]

    return (
        <>
            <h2>{courseName}</h2>
            <PrimeWrapper>
                <TabMenu
                    model = {items}
                    activeIndex={idx}
                    onTabChange={(e) => setIdx(e.index)}
                />
                <DisplayCourseTab idx={idx} labs={labs} courseSlug={courseSlug}/>
            </PrimeWrapper>
        </>
    )
}

function DisplayCourseTab({idx, courseSlug, offeringSlug}){
    if(idx == 0){
        return <StaffCourseSettingsTab courseSlug={courseSlug} offeringSlug={offeringSlug}/>
    }
    
    if(idx == 3){
        return <StaffTeamViewTab  courseSlug={courseSlug}/>
    }

    return (
        <WIP/>
    )
}

function WIP(){
    return (
        <h4>This is a work in progress</h4>
    )
}