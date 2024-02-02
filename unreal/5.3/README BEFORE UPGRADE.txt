"SideFX Labs Unreal Plugin" version 5.1 or newer have adopted a different asset namespace.

Older asset namespaces such as "SideFX ...", "MF ..." have all been updated and unified to "Houdini ...". For instance, "MF_VAT_RigidBodyDynamics" is now called "Houdini_VAT_RigidBodyDynamics." (This is to make it clear to the non-Houdini users on your team, as well as people who are less familiar the name "SideFX", that these assets have a dependency on our plugin.)


== WARNING! ==

We generally DO NOT recommend replacing existing "SideFX Labs Unreal Plugins" in your current UE 5.1-5.3 projects, because the new namespace will break the linking between our Material Functions and your Materials in which those Material Function nodes are used. (It is possible to manually restore those Material Function nodes in your affected Materials, but you have to be very careful.)

If you simply have trouble accessing our right-click menu Scripted Asset Actions (typically used to apply texture presets), you can still safely upgrade your existing "SideFX Labs Unreal Plugin" by updating everything EXCEPT the contents of the ".../Plugins/SideFX_Labs/Content/Materials/" folder.


If you are creating new UE 5.1-5.3 projects, the above warnings do not apply.